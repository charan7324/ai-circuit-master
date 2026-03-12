FROM python:3.9-slim

# 1. Install system-level LaTeX and PNG conversion tools
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    dvipng \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory
WORKDIR /app

# 3. Copy files
COPY . .

# 4. FIX: Upgrade pip and install setuptools/wheel BEFORE the other libraries
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 5. Install the rest of the libraries
RUN pip install --no-cache-dir flask google-generativeai lcapy numpy matplotlib Pillow

# 6. Set Port and Run
ENV PORT=5000
CMD ["python", "app.py"]
