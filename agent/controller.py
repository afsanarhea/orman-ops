"""
ORMÁN-Ops Autonomous Agent Controller (v2)
Custom agent with visible chain-of-thought reasoning.
The LLM decides which tools to call and adapts based on intermediate results.
"""
import json
import time
from typing import Dict, Any, List, Generator, Tuple
from groq import Groq
from agent.tools import (
    fetch_fires, check_weather, assess_regional_risk,
    analyze_threat, plan_response, generate_report,
    KZ_REGIONS,
)

AGENT_SYSTEM_PROMPT = """You are ORMÁN-Ops (ОРМАН-Опс), an autonomous wildfire emergency operations agent for Kazakhstan.

Your mission: Given a region in Kazakhstan, autonomously assess wildfire threats and create an operational response plan.

You have 6 tools available. Call them by responding with a JSON block:

1. **fetch_fires** — Fetch live satellite fire data from NASA FIRMS
   {"tool": "fetch_fires", "reasoning": "why you need this data"}

2. **check_weather** — Get current weather conditions (temperature, wind, humidity)
   {"tool": "check_weather", "reasoning": "why weather data matters here"}

3. **assess_regional_risk** — Evaluate historical fire risk, vegetation type, seasonal factors
   {"tool": "assess_regional_risk", "reasoning": "why regional context is needed"}

4. **analyze_threat** — Combine all data into a threat assessment with confidence score
   {"tool": "analyze_threat", "reasoning": "what data you're synthesizing and why"}

5. **plan_response** — Generate emergency or preventive response plan
   {"tool": "plan_response", "reasoning": "why this plan type is appropriate"}

6. **generate_report** — Compile final operational report
   {"tool": "generate_report", "reasoning": "summarize your findings"}

CRITICAL RULES:
- Always start with fetch_fires to check for active fires.
- After seeing fire data, DECIDE your path:
  * If fires found: check_weather (wind affects spread!) → analyze_threat → plan_response → generate_report
  * If NO fires: check_weather → assess_regional_risk → analyze_threat → plan_response → generate_report
- EXPLAIN your reasoning before each tool call. This is visible to the user.
- Your reasoning should show WHY you're choosing this tool next based on what you've learned so far.
- After generate_report, respond with: {"tool": "done", "summary": "<executive summary in 2-3 sentences>"}
- Be specific in your reasoning. Don't be generic. Reference actual data values you received.

You are analyzing: REGION_PLACEHOLDER

Available regions include priority forest areas like Semey Ormanı (world's largest relict pine forest), Burabay National Park, Bayanaul, and Karkaraly."""


class OrmanAgent:
    def __init__(self, groq_api_key: str, firms_api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=groq_api_key)
        self.firms_api_key = firms_api_key
        self.model = model
        self.conversation: List[Dict] = []
        self.steps: List[Dict] = []
        
        # Tool results storage
        self.firms_result = None
        self.weather_result = None
        self.risk_result = None
        self.threat_result = None
        self.response_plan = None
        self.final_report = None
        self.region = None
        self.confidence = 20  # Starting confidence
    
    def run(self, region: str) -> Generator[Dict[str, Any], None, None]:
        """
        Run the agent autonomously. 
        Yields step dicts: {type, step, tool, reasoning, result, confidence, message}
        """
        self.region = region
        system_prompt = AGENT_SYSTEM_PROMPT.replace("REGION_PLACEHOLDER", region)
        
        self.conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Assess wildfire threats and create an operational plan for: {region}, Kazakhstan. "
                f"Begin your analysis. Remember to explain your reasoning at each step."
            )}
        ]
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # === LLM Reasoning Step ===
                yield {
                    "type": "thinking",
                    "step": iteration,
                    "message": f"Agent reasoning about next action (step {iteration})...",
                    "confidence": self.confidence,
                }
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation,
                    temperature=0.2,
                    max_tokens=800,
                )
                
                assistant_msg = response.choices[0].message.content
                self.conversation.append({"role": "assistant", "content": assistant_msg})
                
                # Parse tool call
                tool_call = self._extract_tool_call(assistant_msg)
                
                if tool_call is None:
                    # LLM didn't produce a tool call — nudge it
                    yield {
                        "type": "reasoning",
                        "step": iteration,
                        "message": assistant_msg[:500],
                        "confidence": self.confidence,
                    }
                    self.conversation.append({
                        "role": "user",
                        "content": "Good reasoning. Now call the next tool. Respond with a JSON tool call."
                    })
                    continue
                
                tool_name = tool_call.get("tool", "")
                reasoning = tool_call.get("reasoning", assistant_msg[:300])
                
                # Check for completion
                if tool_name == "done":
                    yield {
                        "type": "complete",
                        "step": iteration,
                        "message": tool_call.get("summary", "Analysis complete."),
                        "confidence": self.confidence,
                        "report": self.final_report,
                    }
                    return
                
                # === Show reasoning ===
                yield {
                    "type": "reasoning",
                    "step": iteration,
                    "tool": tool_name,
                    "message": reasoning,
                    "confidence": self.confidence,
                }
                
                # === Execute tool ===
                yield {
                    "type": "tool_call",
                    "step": iteration,
                    "tool": tool_name,
                    "message": f"Executing: {tool_name}",
                    "confidence": self.confidence,
                }
                
                result = self._execute_tool(tool_name)
                
                # Update confidence
                self._update_confidence(tool_name, result)
                
                # === Show result ===
                result_summary = self._format_result(tool_name, result)
                
                yield {
                    "type": "tool_result",
                    "step": iteration,
                    "tool": tool_name,
                    "result": result,
                    "result_summary": result_summary,
                    "confidence": self.confidence,
                    "message": result_summary,
                }
                
                # Feed result back to agent
                self.conversation.append({
                    "role": "user",
                    "content": (
                        f"Tool '{tool_name}' returned:\n{result_summary}\n\n"
                        f"Current confidence: {self.confidence}%. "
                        f"Analyze this result and decide your next action. Explain your reasoning."
                    )
                })
                
                self.steps.append({
                    "step": iteration,
                    "tool": tool_name,
                    "reasoning": reasoning,
                    "result_summary": result_summary[:500],
                })
                
                time.sleep(0.3)
                
            except Exception as e:
                yield {
                    "type": "error",
                    "step": iteration,
                    "message": str(e),
                    "confidence": self.confidence,
                }
                self.conversation.append({
                    "role": "user",
                    "content": f"Error: {str(e)}. Skip this step and continue with the next logical tool."
                })
        
        # Max iterations
        if self.final_report:
            yield {
                "type": "complete",
                "step": iteration,
                "message": "Analysis complete (max steps reached).",
                "confidence": self.confidence,
                "report": self.final_report,
            }
    
    def _execute_tool(self, tool_name: str) -> Any:
        if tool_name == "fetch_fires":
            self.firms_result = fetch_fires(self.region, self.firms_api_key)
            return self.firms_result
        
        elif tool_name == "check_weather":
            self.weather_result = check_weather(self.region)
            return self.weather_result
        
        elif tool_name == "assess_regional_risk":
            self.risk_result = assess_regional_risk(self.region)
            return self.risk_result
        
        elif tool_name == "analyze_threat":
            if self.firms_result is None:
                return {"error": "No fire data. Call fetch_fires first."}
            self.threat_result = analyze_threat(
                self.firms_result, self.weather_result, self.risk_result
            )
            return self.threat_result
        
        elif tool_name == "plan_response":
            if self.threat_result is None:
                return {"error": "No threat analysis. Call analyze_threat first."}
            self.response_plan = plan_response(
                self.threat_result, self.weather_result, self.region
            )
            return self.response_plan
        
        elif tool_name == "generate_report":
            if self.threat_result is None:
                return {"error": "Missing threat analysis."}
            self.final_report = generate_report(
                self.region,
                self.firms_result or {},
                self.weather_result or {},
                self.risk_result or {},
                self.threat_result,
                self.response_plan or {},
            )
            return self.final_report
        
        return {"error": f"Unknown tool: {tool_name}"}
    
    def _update_confidence(self, tool_name: str, result: Any):
        if isinstance(result, dict) and result.get("status") == "success":
            increments = {
                "fetch_fires": 20,
                "check_weather": 18,
                "assess_regional_risk": 15,
                "analyze_threat": 20,
                "plan_response": 12,
                "generate_report": 10,
            }
            self.confidence = min(98, self.confidence + increments.get(tool_name, 5))
        elif isinstance(result, dict) and "error" in result:
            self.confidence = max(10, self.confidence - 5)
    
    def _format_result(self, tool_name: str, result: Any) -> str:
        if isinstance(result, dict) and "error" in result:
            return f"ERROR: {result['error']}"
        
        if tool_name == "fetch_fires":
            return (
                f"Region: {result.get('region')} | "
                f"Fires detected: {result.get('fire_count', 0)} | "
                f"Total detections: {result.get('total_detections', 0)} | "
                f"Period: {result.get('period')} | "
                f"Source: {result.get('source', 'VIIRS')}"
                + (f" | Note: {result.get('message', '')}" if result.get('fire_count', 0) == 0 else "")
            )
        elif tool_name == "check_weather":
            c = result.get("current", {})
            fwi = result.get("fire_weather_index", {})
            return (
                f"Temperature: {c.get('temperature_c')}°C | "
                f"Humidity: {c.get('humidity_pct')}% | "
                f"Wind: {c.get('wind_speed_kmh')} km/h ({c.get('wind_direction_compass')}) | "
                f"Gusts: {c.get('wind_gusts_kmh')} km/h | "
                f"Precipitation: {c.get('precipitation_mm')}mm | "
                f"Fire Weather Risk: {fwi.get('risk_level')} ({fwi.get('score')}/100)"
            )
        elif tool_name == "assess_regional_risk":
            r = result.get("risk_assessment", {})
            return (
                f"Risk Level: {r.get('risk_level')} (score: {r.get('overall_risk_score')}/100) | "
                f"Vegetation: {r.get('vegetation_type')} | "
                f"Historical fires: {r.get('historical_fires_per_year')}/year | "
                f"Season: {r.get('season_status')}"
            )
        elif tool_name == "analyze_threat":
            return (
                f"Threat Level: {result.get('threat_level')} | "
                f"Score: {result.get('threat_score')}/100 | "
                f"Confidence: {result.get('confidence_pct')}% | "
                f"Scenario: {result.get('scenario_description')}"
            )
        elif tool_name == "plan_response":
            return (
                f"Plan Type: {result.get('plan_type')} | "
                f"Alert: {result.get('alert_level', '')[:50]}... | "
                f"Actions: {len(result.get('priority_actions', []))} priority items"
            )
        elif tool_name == "generate_report":
            return "Full operational report compiled successfully."
        
        return json.dumps(result, indent=2, default=str)[:500]
    
    def _extract_tool_call(self, text: str) -> Dict | None:
        import re
        patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{"tool":\s*"[^"]+?".*?\})',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if "tool" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
        try:
            parsed = json.loads(text.strip())
            if "tool" in parsed:
                return parsed
        except:
            pass
        return None
