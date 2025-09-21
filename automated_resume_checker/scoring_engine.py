from typing import Dict, Any
import math

class ScoringEngine:
    def __init__(self):
        # Scoring weights - should add up to 1.0
        self.weights = {
            'required_skills': 0.40,    # 40% weight for required skills
            'preferred_skills': 0.15,   # 15% weight for preferred skills  
            'keyword_match': 0.25,      # 25% weight for keyword similarity
            'education_match': 0.10,    # 10% weight for education
            'semantic_match': 0.10      # 10% weight for semantic similarity
        }
    
    def normalize_score(self, score: float, min_val: float = 0, max_val: float = 100) -> float:
        """Normalize score to be between min_val and max_val"""
        if score < 0:
            return min_val
        elif score > max_val:
            return max_val
        return score
    
    def calculate_skills_score(self, match_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate skills-based scores with better scaling"""
        scores = {}
        
        # Required skills score (0-100)
        required_skills = match_results.get('required_skills', {})
        total_required = required_skills.get('total_required', 0)
        matched_required = required_skills.get('total_matched', 0)
        
        if total_required > 0:
            # Base score from exact matches
            base_score = (matched_required / total_required) * 100
            
            # Bonus for high match quality
            match_details = required_skills.get('match_details', {})
            if match_details:
                avg_match_quality = sum(detail.get('score', 0) for detail in match_details.values()) / len(match_details)
                quality_bonus = (avg_match_quality - 70) / 30 * 10  # Up to 10 bonus points
                base_score += max(0, quality_bonus)
            
            scores['required_skills'] = self.normalize_score(base_score)
        else:
            scores['required_skills'] = 50.0  # Neutral score if no requirements
        
        # Preferred skills score (0-100)
        preferred_skills = match_results.get('preferred_skills', {})
        total_preferred = preferred_skills.get('total_required', 0)
        matched_preferred = preferred_skills.get('total_matched', 0)
        
        if total_preferred > 0:
            preferred_score = (matched_preferred / total_preferred) * 100
            scores['preferred_skills'] = self.normalize_score(preferred_score)
        else:
            scores['preferred_skills'] = 60.0  # Slight positive if no preferred skills
        
        return scores
    
    def calculate_keyword_score(self, match_results: Dict[str, Any]) -> float:
        """Calculate keyword match score with better scaling"""
        keyword_match = match_results.get('keyword_match', {})
        similarity_score = keyword_match.get('similarity_score', 0)
        
        # Scale TF-IDF similarity (usually 0-1) to 0-100 with curve adjustment
        if similarity_score > 0:
            # Apply logarithmic scaling to make low similarities more meaningful
            scaled_score = (math.log10(similarity_score * 10 + 1) / math.log10(11)) * 100
            return self.normalize_score(scaled_score)
        
        return 20.0  # Base score even with no matches
    
    def calculate_education_score(self, match_results: Dict[str, Any]) -> float:
        """Calculate education match score"""
        education_match = match_results.get('education_match', {})
        total_qualifications = education_match.get('total_required', 0)
        matched_qualifications = education_match.get('total_matched', 0)
        
        if total_qualifications > 0:
            education_score = (matched_qualifications / total_qualifications) * 100
            return self.normalize_score(education_score)
        else:
            return 70.0  # Neutral-positive score if no education requirements
    
    def calculate_semantic_score(self, match_results: Dict[str, Any]) -> float:
        """Calculate semantic match score with better scaling"""
        semantic_match = match_results.get('semantic_match', {})
        semantic_score = semantic_match.get('semantic_score', 0)
        
        # Apply similar scaling as keyword score
        if semantic_score > 0:
            scaled_score = (math.log10(semantic_score * 10 + 1) / math.log10(11)) * 100
            return self.normalize_score(scaled_score)
        
        return 25.0  # Base score even with no matches
    
    def apply_bonus_penalties(self, base_score: float, match_results: Dict[str, Any]) -> float:
        """Apply bonuses and penalties to adjust final score"""
        final_score = base_score
        
        # Bonus for having many skills match
        required_skills = match_results.get('required_skills', {})
        matched_count = required_skills.get('total_matched', 0)
        
        if matched_count >= 5:
            final_score += 5  # Bonus for matching many skills
        elif matched_count >= 3:
            final_score += 2
        
        # Penalty for missing critical requirements
        missing_skills = required_skills.get('missing_skills', [])
        critical_missing = len([skill for skill in missing_skills if any(word in skill.lower() 
                               for word in ['python', 'java', 'sql', 'react', 'required', 'must'])])
        
        if critical_missing > 0:
            final_score -= (critical_missing * 3)  # Penalty for missing critical skills
        
        # Bonus for keyword richness
        keyword_match = match_results.get('keyword_match', {})
        common_terms = keyword_match.get('common_terms', [])
        if len(common_terms) > 10:
            final_score += 3
        elif len(common_terms) > 5:
            final_score += 1
        
        return self.normalize_score(final_score, 15, 100)  # Minimum 15, max 100
    
    def determine_verdict(self, final_score: float) -> str:
        """Determine hiring verdict based on score"""
        if final_score >= 75:
            return "High"
        elif final_score >= 45:
            return "Medium" 
        else:
            return "Low"
    
    def generate_score_breakdown(self, match_results: Dict[str, Any], hard_score: float, semantic_score: float) -> Dict[str, Any]:
        """Generate comprehensive score breakdown with proper scaling"""
        
        # Calculate individual component scores
        skills_scores = self.calculate_skills_score(match_results)
        keyword_score = self.calculate_keyword_score(match_results)
        education_score = self.calculate_education_score(match_results)
        semantic_score_normalized = self.calculate_semantic_score(match_results)
        
        # Calculate weighted final score
        component_scores = {
            'required_skills': skills_scores.get('required_skills', 0),
            'preferred_skills': skills_scores.get('preferred_skills', 0),
            'keyword_match': keyword_score,
            'education_match': education_score,
            'semantic_match': semantic_score_normalized
        }
        
        # Weighted average
        weighted_score = sum(
            component_scores[component] * self.weights[component] 
            for component in component_scores
        )
        
        # Apply bonuses/penalties
        final_score = self.apply_bonus_penalties(weighted_score, match_results)
        
        # Ensure minimum reasonable score for any resume
        final_score = max(final_score, 15.0)
        
        # Generate verdict
        verdict = self.determine_verdict(final_score)
        
        return {
            'relevance_score': round(final_score, 2),
            'hard_match_score': round(component_scores['required_skills'], 2),
            'semantic_score': round(semantic_score_normalized, 2),
            'verdict': verdict,
            'component_scores': {
                'required_skills': round(component_scores['required_skills'], 2),
                'preferred_skills': round(component_scores['preferred_skills'], 2),
                'keyword_match': round(keyword_score, 2),
                'education_match': round(education_score, 2),
                'semantic_match': round(semantic_score_normalized, 2)
            },
            'weights_used': self.weights
        }
    
    def explain_score(self, score_data: Dict[str, Any]) -> str:
        """Generate human-readable explanation of the score"""
        final_score = score_data['relevance_score']
        verdict = score_data['verdict']
        components = score_data['component_scores']
        
        explanation = f"Overall Score: {final_score}/100 ({verdict} suitability)\n\n"
        explanation += "Score Breakdown:\n"
        explanation += f"• Required Skills: {components['required_skills']}/100 (40% weight)\n"
        explanation += f"• Preferred Skills: {components['preferred_skills']}/100 (15% weight)\n"
        explanation += f"• Keyword Match: {components['keyword_match']}/100 (25% weight)\n"
        explanation += f"• Education Match: {components['education_match']}/100 (10% weight)\n"
        explanation += f"• Semantic Match: {components['semantic_match']}/100 (10% weight)\n\n"
        
        if verdict == "High":
            explanation += "✅ Strong candidate - recommended for interview"
        elif verdict == "Medium":
            explanation += "⚠️ Moderate match - consider for second review"
        else:
            explanation += "❌ Low match - may not meet requirements"
        
        return explanation
