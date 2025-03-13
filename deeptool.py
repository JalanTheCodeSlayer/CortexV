import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openai
import json
import re
import time
from typing import Optional, List, Dict, Any
import subprocess
import socket
import requests
from bs4 import BeautifulSoup

# Streamlit Page Configuration
st.set_page_config(
    page_title="CORTEX V",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Styling
CUSTOM_CSS = """
<style>
/* Hide header icons */
[data-testid="stHeaderActionElements"] {
    display: none !important;
}

/* Main container styling */
[data-testid="stAppViewContainer"] {
    background: #F9F9FB;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: start;
    align-items: center;
    text-align: center;
    padding: 20px;
}

/* Main content wrapper */
.main-content {
    width: 100%;
    max-width: 900px;
    margin: 0 auto;
    text-align: center;
}

/* Fixed header styling */
[data-testid="stHeader"] {
    background-color: #FFFFFF !important;
    color: #333333 !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    width: 100%;
    position: fixed;
    top: 0;
    z-index: 100;
}

[data-testid="stHeader"] .css-1avcm0n,
[data-testid="stHeader"] .css-1q8df74,
[data-testid="stHeader"] .css-1fcv3bd {
    display: none !important;
}

[data-testid="stHeader"] a {
    color: #8A2BE2 !important;
    font-weight: 700;
    text-decoration: none;
    padding: 0 10px;
}

[data-testid="stHeader"] a:hover {
    color: #7a1bd2 !important;
}

/* Typography */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
body, .markdown-text-container {
    font-family: 'Orbitron', sans-serif;
    color: #333333;
    font-weight: 400;
    line-height: 1.6;
}

/* Header title styling */
h1 {
    color: #8A2BE2 !important;
    font-weight: 700;
    text-shadow: 0 0 15px #8A2BE2, 0 0 25px #8A2BE2, 0 0 40px #D8BFD8;
    transition: text-shadow 0.3s ease;
    letter-spacing: 2px;
    margin-bottom: 10px;
    margin-top: 60px; /* Space for fixed header */
    text-align: center;
    width: 100%;
}

h1:hover {
    text-shadow: 0 0 20px #8A2BE2, 0 0 30px #8A2BE2, 0 0 50px #D8BFD8;
}

/* Subheader styling */
h2 {
    color: #4B0082 !important;
    font-weight: 400;
    font-size: 1.2em;
    margin-bottom: 20px;
}

/* Button styling */
.stButton>button {
    background: linear-gradient(90deg, #8A2BE2, #D8BFD8);
    color: #FFFFFF;
    border: none;
    padding: 12px 30px;
    font-size: 16px;
    font-family: 'Orbitron', sans-serif;
    border-radius: 50px;
    box-shadow: 0 2px 10px rgba(138, 43, 226, 0.2);
    transition: all 0.3s ease;
    letter-spacing: 1px;
    margin: 20px auto;
    display: block;
}

.stButton>button:hover {
    background: linear-gradient(90deg, #7a1bd2, #C9A0DC);
    box-shadow: 0 4px 15px rgba(138, 43, 226, 0.4);
    transform: translateY(-2px);
}

/* Footer styling */
.footer {
    text-align: center;
    color: #8A2BE2;
    margin-top: 30px;
    font-size: 12px;
    font-weight: 400;
    letter-spacing: 1px;
    width: 100%;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# OpenAI API Key (Replace or manage via st.secrets)
OPENAI_API_KEY = "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"  # Replace or manage securely"
openai.api_key = OPENAI_API_KEY

# Prompt
COMPANY_SEARCH_PROMPT = (
    "Find 5 companies domains: fintech firms, companies with supply chain vulnerabilities, "
    "industries frequently targeted by ransomware (e.g., government agencies, manufacturing, healthcare, small businesses), "
    "and companies facing evolving cyber threats. "
    "Provide a JSON list where each item is a dictionary with the keys: 'sector', 'company_name' (if available), and 'domain'."
)

def deep_search(prompt: str) -> Optional[str]:
    try:
        time.sleep(2)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def parse_json_response(response: str) -> Optional[List[Dict[str, Any]]]:
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, response, re.DOTALL)
    if match:
        response_text = match.group(1)
    else:
        response_text = response
    
    for _ in range(3):
        try:
            return json.loads(response_text)
        except:
            time.sleep(1)
    return None

def nmap_scan(domain: str) -> Dict[str, Any]:
    try:
        ip = socket.gethostbyname(domain)
        result = subprocess.run(['nmap', '-F', ip], capture_output=True, text=True, timeout=60)
        open_ports = []
        vulnerabilities = []

        for line in result.stdout.split('\n'):
            if '/tcp' in line and 'open' in line:
                port = line.split('/')[0]
                service = line.split('open')[1].strip()
                open_ports.append({'port': port, 'service': service})
                if port in ['21', '22', '23', '445']:
                    vulnerabilities.append(
                        f"Potentially vulnerable service on port {port}: {service}"
                    )
        return {
            "ip": ip,
            "open_ports": open_ports,
            "vulnerabilities": vulnerabilities,
            "error": None,
        }
    except Exception as e:
        return {
            "ip": None,
            "open_ports": [],
            "vulnerabilities": [],
            "error": str(e),
        }

def check_http_vulnerabilities(domain: str) -> List[str]:
    vuln = []
    try:
        for protocol in ["http", "https"]:
            url = f"{protocol}://{domain}"
            try:
                r = requests.get(url, timeout=5)
                server = r.headers.get("Server", "")
                if "Apache/2.2" in server or "IIS/6" in server:
                    vuln.append(f"Outdated server detected: {server}")
                if protocol == "http" and r.status_code == 200:
                    vuln.append("HTTP accessible - no HTTPS enforcement")
                soup = BeautifulSoup(r.text, "html.parser")
                if soup.find("input", {"name": "q"}) and not soup.find(
                    "meta", {"http-equiv": "Content-Security-Policy"}
                ):
                    vuln.append("Potential XSS vulnerability - no CSP header")
            except:
                pass
    except Exception as e:
        vuln.append(f"HTTP check error: {e}")
    return vuln

SPINNER_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Particle Spinner</title>
  <style>
    body { margin: 0; background: transparent; }
    .particle-spinner {
      position: relative;
      width: 120px;
      height: 120px;
      margin: auto;
    }
    .particle-spinner div {
      position: absolute;
      border: 4px solid #8A2BE2;
      opacity: 1;
      border-radius: 50%;
      animation: particle 1.5s cubic-bezier(0, 0.2, 0.8, 1) infinite;
    }
    .particle-spinner div:nth-child(2) { animation-delay: -0.75s; }
    @keyframes particle {
      0% {
        top: 60px; left: 60px;
        width: 0; height: 0;
        opacity: 1;
      }
      100% {
        top: 0; left: 0;
        width: 120px; height: 120px;
        opacity: 0;
      }
    }
  </style>
</head>
<body>
  <div class="particle-spinner">
    <div></div>
    <div></div>
  </div>
</body>
</html>
"""

def table_to_iframe_html(df: pd.DataFrame, scan_results: Dict[str, Dict]) -> str:
    df = df.copy()
    df['open_ports'] = df['domain'].apply(
        lambda x: ', '.join([p['port'] for p in scan_results.get(x, {}).get('open_ports', [])]) or 'None'
    )
    df['vulnerabilities'] = df['domain'].apply(
        lambda x: '<br>'.join(scan_results.get(x, {}).get('vulnerabilities', [])) or 'None'
    )
    table_html = df.to_html(index=False, escape=False)
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
    body {{ margin: 0; background: transparent; font-family: sans-serif; color: #333; }}
    h3 {{ text-align: center; margin-top: 1em; }}
    table {{ margin: 1em auto; border-collapse: collapse; width: 90%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    </style>
</head>
<body>
    <h3>Parsed Companies & Vulnerability Scan</h3>
    {table_html}
</body>
</html>
"""

def main():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Create placeholders so we can remove them later.
    title_placeholder = st.empty()
    desc_placeholder = st.empty()
    button_placeholder = st.empty()

    with title_placeholder:
        st.header("CORTEX V", anchor=False)
    with desc_placeholder:
        st.markdown("Some introduction or instructions here, so the page doesn't look empty.")

    # The scan button
    if button_placeholder.button("Scan Domain"):
        # Remove the title, description, and button
        title_placeholder.empty()
        desc_placeholder.empty()
        button_placeholder.empty()

        # Show spinner
        spinner_placeholder = st.empty()
        with spinner_placeholder:
            components.html(SPINNER_HTML, height=150)

        # 1) Fetch data
        response = deep_search(COMPANY_SEARCH_PROMPT)
        if not response:
            st.error("No response from API.")
            spinner_placeholder.empty()
            return

        companies = parse_json_response(response)
        if not companies:
            st.error("Failed to parse company JSON.")
            spinner_placeholder.empty()
            return
        
        df = pd.DataFrame(companies)
        if not all(col in df.columns for col in ["sector","company_name","domain"]):
            st.error("Missing required columns in response.")
            spinner_placeholder.empty()
            return

        # 2) Perform scanning
        scan_results = {}
        for domain in df['domain']:
            nmap_info = nmap_scan(domain)
            http_info = check_http_vulnerabilities(domain)
            nmap_info['vulnerabilities'].extend(http_info)
            scan_results[domain] = nmap_info

        # Remove spinner
        spinner_placeholder.empty()

        # 3) Show final results
        final_html = table_to_iframe_html(df, scan_results)
        st.components.v1.html(final_html, height=600, scrolling=True)

    st.markdown('<div class="footer">CORTEX V | Powered by Cortex V © 2025</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
