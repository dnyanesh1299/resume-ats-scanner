"""Create a sample resume PDF for testing."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pathlib import Path

def main():
    output = Path(__file__).parent / "sample_data" / "sample_resume.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(str(output), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("John Doe", styles["Title"]))
    story.append(Paragraph("john.doe@email.com | (555) 123-4567 | linkedin.com/in/johndoe | github.com/johndoe", styles["Normal"]))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph("Senior Software Engineer with 5+ years of experience in Python, Machine Learning, and NLP. Expertise in building production ML systems.", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Skills", styles["Heading2"]))
    story.append(Paragraph("Python, Machine Learning, Deep Learning, NLP, PyTorch, TensorFlow, REST APIs, AWS, Docker, Kubernetes, SQL, PostgreSQL, MongoDB", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Experience", styles["Heading2"]))
    story.append(Paragraph("Senior ML Engineer | Tech Corp | 2020 - Present", styles["Normal"]))
    story.append(Paragraph("• Developed NLP pipelines using spaCy and Hugging Face Transformers", styles["Normal"]))
    story.append(Paragraph("• Built REST APIs with FastAPI for model serving", styles["Normal"]))
    story.append(Paragraph("• Deployed models on AWS with Docker and Kubernetes", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Software Engineer | Data Inc | 2018 - 2020", styles["Normal"]))
    story.append(Paragraph("• Implemented ML models with PyTorch and Scikit-learn", styles["Normal"]))
    story.append(Paragraph("• Designed ETL pipelines using Apache Spark", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Education", styles["Heading2"]))
    story.append(Paragraph("M.S. Computer Science | State University | 2018", styles["Normal"]))
    story.append(Paragraph("B.S. Computer Science | State University | 2016", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Projects", styles["Heading2"]))
    story.append(Paragraph("Resume ATS Scanner - Built NLP-based resume parser using spaCy and sentence-transformers", styles["Normal"]))
    
    doc.build(story)
    print(f"Created {output}")

if __name__ == "__main__":
    main()
