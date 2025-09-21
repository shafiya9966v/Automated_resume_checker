import openai
from typing import Dict, List, Any
import os

class LLMFeedbackGenerator:
    def __init__(self, api_key: str = None):
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv('OPENAI_API_KEY')
    
    def generate_feedback(self, resume_data: Dict[str, Any], job_data: Dict[str, Any], 
                         match_results: Dict[str, Any], score_data: Dict[str, Any]) -> str:
        """Generate personalized feedback using OpenAI API"""
        
        missing_skills = match_results['required_skills']['missing_skills']
        matched_skills = match_results['required_skills']['matched_skills']
        relevance_score = score_data['relevance_score']
        verdict = score_data['verdict']
        
        prompt = f"""
        As a career counselor, provide personalized feedback for a job candidate.
        
        Job Role: {job_data.get('title', 'N/A')}
        Candidate: {resume_data.get('candidate_name', 'Candidate')}
        Overall Score: {relevance_score}/100 ({verdict} suitability)
        
        Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}
        Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}
        
        Provide constructive feedback in 3 sections:
        1. Strengths (what they did well)
        2. Areas for Improvement (missing skills/experience)
        3. Actionable Recommendations (specific steps to improve)
        
        Keep it professional, encouraging, and specific.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful career counselor providing constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            # Fallback feedback if API fails
            return self.generate_fallback_feedback(missing_skills, matched_skills, verdict)
    
    def generate_fallback_feedback(self, missing_skills: List[str], 
                                  matched_skills: List[str], verdict: str) -> str:
        """Generate basic feedback without LLM"""
        feedback = f"**Assessment: {verdict} Suitability**\n\n"
        
        if matched_skills:
            feedback += f"**Strengths:**\n"
            feedback += f"You have relevant skills including: {', '.join(matched_skills[:5])}\n\n"
        
        if missing_skills:
            feedback += f"**Areas for Improvement:**\n"
            feedback += f"Consider developing these skills: {', '.join(missing_skills[:5])}\n\n"
        
        feedback += f"**Recommendations:**\n"
        feedback += f"- Focus on acquiring the missing technical skills\n"
        feedback += f"- Update your resume to highlight relevant projects\n"
        feedback += f"- Consider relevant certifications or online courses"
        
        return feedback
