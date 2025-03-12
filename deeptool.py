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

# Custom CSS for Styling (Google Fonts import removed for testing)
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
    justify-content: center;
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
body, .markdown-text-container {
    font-family: sans-serif;
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
    font-family: sans-serif;
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

# API Configuration
OPENAI_API_KEY = "jina_19bae2a4d32e449189da4ce64c75d788DYhR7j6rVLfP4g82NBkUQlcoEcJu"
openai.api_key = OPENAI_API_KEY
openai.api_base = "https://deepsearch.jina.ai/v1"

# Company Search Prompt
COMPANY_SEARCH_PROMPT = (
    "Find 5 companies domains: fintech firms, companies with supply chain vulnerabilities, "
    "industries frequently targeted by ransomware (e.g., government agencies, manufacturing, healthcare, small businesses), "
    "and companies facing evolving cyber threats. "
    "Provide a JSON list where each item is a dictionary with the keys: 'sector', 'company_name' (if available), and 'domain'."
)

# API Interaction Functions
def deep_search(prompt: str) -> Optional[str]:
    """Send a prompt to the Jina DeepSearch API and return the response content."""
    try:
        time.sleep(6)
        response = openai.ChatCompletion.create(
            model="jina-deepsearch-v1",
            messages=[{"role": "user", "content": prompt}]
        )
        # Debug: print the raw API response
        st.write("Raw API response:", response)
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def parse_json_response(response: str) -> Optional[List[Dict[str, Any]]]:
    """Parse JSON from the API response with retry logic, handling code blocks or raw JSON."""
    if not isinstance(response, str):
        st.warning("Invalid response format: Response is not a string")
        return None

    code_block_pattern = r"```json\s*(.*?)\s*```"
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        try:
            match = re.search(code_block_pattern, response, re.DOTALL)
            json_str = match.group(1) if match else response
            parsed_data = json.loads(json_str)
            # Debug: print parsed JSON data
            st.write("Parsed JSON data:", parsed_data)
            return parsed_data
            
        except json.JSONDecodeError as e:
            attempts += 1
            st.warning(f"Attempt {attempts} failed to parse JSON: {str(e)}")
            if attempts == max_attempts:
                st.error("Failed to parse JSON after 3 attempts. Please try again.")
                return None
            time.sleep(1)  # Brief delay before retrying
        except Exception as e:
            st.warning(f"Unexpected error on attempt {attempts + 1}: {str(e)}")
            attempts += 1
            if attempts == max_attempts:
                st.error("Failed to parse JSON after 3 attempts due to unexpected errors.")
                return None
            time.sleep(1)

# Vulnerability Scanning Functions
def nmap_scan(domain: str) -> Dict[str, Any]:
    """Perform a basic Nmap scan on the domain."""
    try:
        # Resolve domain to IP
        ip = socket.gethostbyname(domain)
        # Basic Nmap scan for open ports (-F for fast scan)
        result = subprocess.run(['nmap', '-F', ip], capture_output=True, text=True, timeout=60)
        
        # Debug: log the raw nmap output
        st.write(f"Nmap output for {domain} ({ip}):", result.stdout)
        
        open_ports = []
        vulnerabilities = []
        
        # Parse Nmap output
        for line in result.stdout.split('\n'):
            if '/tcp' in line and 'open' in line:
                port = line.split('/')[0]
                service = line.split('open')[1].strip()
                open_ports.append({'port': port, 'service': service})
                
                # Basic vulnerability check based on common ports
                if port in ['21', '22', '23', '445']:
                    vulnerabilities.append(f"Potentially vulnerable service on port {port}: {service}")
        
        return {
            'ip': ip,
            'open_ports': open_ports,
            'vulnerabilities': vulnerabilities,
            'error': None
        }
    except Exception as e:
        st.error(f"Error during nmap_scan for {domain}: {str(e)}")
        return {
            'ip': None,
            'open_ports': [],
            'vulnerabilities': [],
            'error': str(e)
        }

def check_http_vulnerabilities(domain: str) -> List[str]:
    """Check for basic HTTP-related vulnerabilities."""
    vulnerabilities = []
    try:
        # Try both HTTP and HTTPS
        for protocol in ['http', 'https']:
            url = f"{protocol}://{domain}"
            try:
                response = requests.get(url, timeout=5)
                
                # Check for outdated server headers
                server = response.headers.get('Server', '')
                if 'Apache/2.2' in server or 'IIS/6' in server:
                    vulnerabilities.append(f"Outdated server detected: {server}")
                
                # Check if HTTPS is not enforced
                if protocol == 'http' and response.status_code == 200:
                    vulnerabilities.append("HTTP accessible - no HTTPS enforcement")
                
                # Basic XSS check
                soup = BeautifulSoup(response.text, 'html.parser')
                if soup.find('input', {'name': 'q'}) and not soup.find('meta', {'http-equiv': 'Content-Security-Policy'}):
                    vulnerabilities.append("Potential XSS vulnerability - no CSP header")
                    
            except requests.RequestException as e:
                st.write(f"HTTP request error for {url}: {str(e)}")
                continue
    except Exception as e:
        vulnerabilities.append(f"HTTP check error: {str(e)}")
    
    return vulnerabilities

# Particle Spinner HTML
PARTICLE_SPINNER_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Particle Spinner</title>
  <style>
    body {
      margin: 0;
      background: transparent;
    }
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
    .particle-spinner div:nth-child(2) {
      animation-delay: -0.75s;
    }
    @keyframes particle {
      0% {
        top: 60px;
        left: 60px;
        width: 0;
        height: 0;
        opacity: 1;
      }
      100% {
        top: 0;
        left: 0;
        width: 120px;
        height: 120px;
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

# HTML Table Generation
def table_to_iframe_html(df: pd.DataFrame, scan_results: Dict[str, Dict]) -> str:
    """Convert DataFrame and scan results to HTML table."""
    # Create a copy with original columns
    display_df = df.copy()
    display_df['open_ports'] = display_df['domain'].apply(
        lambda x: ', '.join([p['port'] for p in scan_results.get(x, {}).get('open_ports', [])]) or 'None'
    )
    display_df['vulnerabilities'] = display_df['domain'].apply(
        lambda x: '<br>'.join(scan_results.get(x, {}).get('vulnerabilities', [])) or 'None'
    )
    
    table_html = display_df.to_html(index=False, escape=False)
    
    # Debug: output the HTML table string
    st.code(table_html, language="html")
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
    body {{
        margin: 0;
        background: transparent;
        font-family: sans-serif;
        color: #333;
    }}
    h3 {{
        text-align: center;
        margin-top: 1em;
    }}
    table {{
        margin: 1em auto;
        border-collapse: collapse;
        width: 90%;
    }}
    th, td {{
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }}
    </style>
</head>
<body>
    <h3>Parsed Companies & Vulnerability Scan</h3>
    {table_html}
</body>
</html>
"""

# Main Application Logic
def main():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    title_ph = st.empty()
    button_ph = st.empty()
    
    with title_ph:
        st.header("CORTEX V", anchor=False)
    
    with button_ph:
        if st.button("Scan Domain"):
            title_ph.empty()
            button_ph.empty()
            
            spinner_ph = st.empty()
            with spinner_ph:
                components.html(
                    PARTICLE_SPINNER_HTML,
                    height=150,
                    scrolling=False
                )
            
            # Get company data
            response = deep_search(COMPANY_SEARCH_PROMPT)
            if response:
                companies = parse_json_response(response)
                if companies:
                    # Debug: output the parsed companies list
                    st.write("Parsed companies:", companies)
                    
                    df = pd.DataFrame(companies)
                    st.write("DataFrame preview:", df)
                    required_cols = ['sector', 'company_name', 'domain']
                    if not all(col in df.columns for col in required_cols):
                        st.error("Data missing required columns")
                    else:
                        # Perform vulnerability scans
                        scan_results = {}
                        with spinner_ph:
                            st.write("Scanning for vulnerabilities...")
                        for domain in df['domain']:
                            st.write(f"Scanning domain: {domain}")
                            nmap_result = nmap_scan(domain)
                            st.write(f"nmap result for {domain}:", nmap_result)
                            http_vulns = check_http_vulnerabilities(domain)
                            nmap_result['vulnerabilities'].extend(http_vulns)
                            scan_results[domain] = nmap_result
                        
                        # Debug: output complete scan_results
                        st.write("Complete scan_results:", scan_results)
                        
                        spinner_ph.empty()
                        table_html = table_to_iframe_html(df, scan_results)
                        # Debug: Check if the HTML is generated and then display it
                        st.write("Rendering HTML table...")
                        components.html(table_html, height=600, scrolling=True)
                else:
                    spinner_ph.empty()
                    st.error("Unable to parse company data.")
            else:
                spinner_ph.empty()
                st.error("Failed to fetch data. Please check your connection.")
        
    st.markdown(
        '<div class="footer">CORTEX V | Powered by Cortex V © 2025</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
