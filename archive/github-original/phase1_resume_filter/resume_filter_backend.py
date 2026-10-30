import re
import os
from typing import List, Dict, Any
import warnings
import PyPDF2
import spacy
from collections import Counter

warnings.filterwarnings('ignore')


class ResumeParser:

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def extract_name(self, text: str) -> str:
        """Extract candidate name using NER"""
        doc = self.nlp(text[:1000])  # Process first 1000 chars

        # Look for PERSON entities in the first few lines
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text

        # Fallback: Look for capitalized words at the start
        lines = text.split('\n')
        for line in lines[:5]:
            words = line.strip().split()
            if len(words) >= 2 and words[0].istitle() and words[1].istitle():
                return ' '.join(words[:2])

        return "Unknown"

    def extract_email(self, text: str) -> str:
        """Extract email address using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else "Not found"

    def extract_phone(self, text: str) -> str:
        """Extract phone number using regex"""
        # Various phone formats
        phone_patterns = [
            r'\+?\d{1,3}[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}',
            r'\d{10}',
            r'\(\d{3}\)\s*\d{3}[-\s]?\d{4}'
        ]

        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]

        return "Not found"

    def extract_skills(self, text: str, key_terms: List[str]) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []

        for term in key_terms:
            # Check if term exists in text (case insensitive)
            if term.lower() in text_lower:
                found_skills.append(term)

        # Also extract using spaCy NER for technologies
        doc = self.nlp(text)
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            for term in key_terms:
                if term.lower() in chunk_text and term not in found_skills:
                    found_skills.append(term)

        return list(set(found_skills))

    def extract_education(self, text: str) -> str:
        """Extract education degree"""
        degrees = [
            'Ph.D', 'PhD', 'Master', 'M.S.', 'M.Tech', 'MBA', 'M.A.',
            'Bachelor', 'B.S.', 'B.Tech', 'B.E.', 'B.A.'
        ]

        text_lower = text.lower()
        for degree in degrees:
            if degree.lower() in text_lower:
                return degree

        return "Not specified"

    def extract_experience(self, text: str) -> str:
        """Extract years of experience"""
        # Look for patterns like "5 years", "3+ years", etc.
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
            r'experience\s*:?\s*(\d+)\+?\s*years?'
        ]

        for pattern in exp_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return f"{matches[0]} years"

        return "Not specified"

    def calculate_match_score(self, resume_skills: List[str],
                              key_terms: List[str]) -> float:
        """Calculate how well resume matches key terms"""
        if not key_terms:
            return 0.0

        matched_terms = len(resume_skills)
        total_terms = len(key_terms)

        # Base score from matched terms
        base_score = (matched_terms / total_terms) * 100

        # Bonus for having more matched terms
        bonus = min(matched_terms * 2, 20)

        final_score = min(base_score + bonus, 100)
        return round(final_score, 2)

    def parse_resume(self, pdf_path: str, key_terms: List[str]) -> Dict[str, Any]:
        """Parse a single resume and extract all information"""
        text = self.extract_text_from_pdf(pdf_path)

        if not text:
            return {
                'filename': os.path.basename(pdf_path),
                'error': 'Failed to extract text from PDF'
            }

        # Extract all information
        name = self.extract_name(text)
        email = self.extract_email(text)
        phone = self.extract_phone(text)
        skills = self.extract_skills(text, key_terms)
        education = self.extract_education(text)
        experience = self.extract_experience(text)
        match_score = self.calculate_match_score(skills, key_terms)

        return {
            'filename': os.path.basename(pdf_path),
            'name': name,
            'email': email,
            'phone': phone,
            'skills': skills,
            'education': education,
            'experience': experience,
            'match_score': match_score,
            'raw_text_length': len(text)
        }


class ResumeFilter:

    def __init__(self):
        self.parser = ResumeParser()

    def load_key_terms(self, key_terms_file: str) -> List[str]:
        """Load key terms from text file"""
        try:
            with open(key_terms_file, 'r') as f:
                terms = [line.strip() for line in f if line.strip()]
            return terms
        except Exception as e:
            print(f"Error loading key terms: {e}")
            return []

    def process_resumes(self, resume_files: List[str],
                        key_terms_file: str,
                        role: str,
                        min_score: float = 50.0) -> List[Dict[str, Any]]:
        """Process multiple resumes and filter by criteria"""

        # Load key terms
        key_terms = self.load_key_terms(key_terms_file)

        if not key_terms:
            print("No key terms found!")
            return []

        print(f"\nProcessing resumes for role: {role}")
        print(f"Key terms: {', '.join(key_terms)}")
        print(f"Number of resumes: {len(resume_files)}")
        print("=" * 60)

        # Parse all resumes
        results = []
        for idx, resume_file in enumerate(resume_files, 1):
            print(f"\nProcessing {idx}/{len(resume_files)}: {resume_file}")

            parsed_data = self.parser.parse_resume(resume_file, key_terms)
            parsed_data['role'] = role
            results.append(parsed_data)

            print(f"  Name: {parsed_data.get('name', 'Unknown')}")
            print(f"  Match Score: {parsed_data.get('match_score', 0)}%")
            print(f"  Skills Found: {len(parsed_data.get('skills', []))}")

        # Sort by match score (highest first)
        results.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        # Filter by minimum score
        filtered_results = [r for r in results if r.get('match_score', 0) >= min_score]

        print("\n" + "=" * 60)
        print(f"\nFiltered Results: {len(filtered_results)}/{len(results)} candidates")
        print(f"(Minimum score: {min_score}%)\n")

        return filtered_results

    def save_results(self, results: List[Dict[str, Any]], output_file: str = 'filtered_resumes.txt'):
        """Save filtered results to a text file"""
        try:
            with open(output_file, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("SMARTHIRE - FILTERED RESUME RESULTS\n")
                f.write("=" * 80 + "\n\n")

                for idx, candidate in enumerate(results, 1):
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"CANDIDATE #{idx}\n")
                    f.write(f"{'=' * 80}\n")
                    f.write(f"Name: {candidate.get('name', 'Unknown')}\n")
                    f.write(f"Email: {candidate.get('email', 'Not found')}\n")
                    f.write(f"Phone: {candidate.get('phone', 'Not found')}\n")
                    f.write(f"Education: {candidate.get('education', 'Not specified')}\n")
                    f.write(f"Experience: {candidate.get('experience', 'Not specified')}\n")
                    f.write(f"Match Score: {candidate.get('match_score', 0)}%\n")
                    f.write(f"Role: {candidate.get('role', 'N/A')}\n")
                    f.write(f"Source File: {candidate.get('filename', 'Unknown')}\n")
                    f.write(f"\nMatched Skills: {', '.join(candidate.get('skills', ['None']))}\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")

            print(f"\nResults saved to: {output_file}")
            return True
        except Exception as e:
            print(f"Error saving results: {e}")
            return False


def main():
    print("=" * 60)
    print("SmartHire Resume Filter - NLP Prototype")
    print("=" * 60)

    # Initialize filter
    resume_filter = ResumeFilter()

    # Example: Process resumes
    resume_files = [
        'resume_alex_johnson.pdf',
        'resume_david_lee.pdf',
        'resume_maria_garcia.pdf',
        'resume_john_doe.pdf',
        'resume_jane_smith.pdf'
    ]

    key_terms_file = 'key_terms_sample.txt'
    role = 'Software Engineer'

    # Check if files exist
    existing_files = [f for f in resume_files if os.path.exists(f)]

    if not existing_files:
        print("\nNo resume files found. Please add PDF resumes to the directory.")
        print("Expected files: resume1.pdf, resume2.pdf, etc.")
        return

    if not os.path.exists(key_terms_file):
        print(f"\nKey terms file '{key_terms_file}' not found.")
        print("Creating sample key terms file...")

        sample_terms = [
            'Python',
            'Machine Learning',
            'Data Science',
            'TensorFlow',
            'AWS',
            'SQL',
            'Docker',
            'Git'
        ]

        with open(key_terms_file, 'w') as f:
            f.write('\n'.join(sample_terms))

        print(f"Sample key terms file created with: {', '.join(sample_terms)}")

    results = resume_filter.process_resumes(
        existing_files,
        key_terms_file,
        role,
        min_score=40.0
    )

    if results:
        resume_filter.save_results(results)

        print("\n" + "=" * 60)
        print("TOP CANDIDATES:")
        print("=" * 60)
        for idx, candidate in enumerate(results[:5], 1):
            print(f"{idx}. {candidate.get('name')} - {candidate.get('match_score')}% match")
    else:
        print("\nNo candidates met the minimum criteria.")


if __name__ == "__main__":
    main()
