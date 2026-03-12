FROM python:3.9-slim

# Install minimal LaTeX and PNG conversion tools
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    dvipng \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir flask google-generativeai lcapy numpy matplotlib Pillow

ENV PORT=5000
CMD ["python", "app.py"]