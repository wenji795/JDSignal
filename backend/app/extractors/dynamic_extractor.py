"""
动态关键词提取模块 - 不依赖预定义字典，从文本中动态提取技术术语
"""
import re
from typing import List, Dict, Set, Tuple
from collections import defaultdict


# 常见技术术语模式
TECH_PATTERNS = [
    # 驼峰命名（如 ReactJS, NodeJS）
    r'\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b',
    # 全大写缩写（如 API, CI/CD, AWS, SQL）
    r'\b[A-Z]{2,}(?:[/-][A-Z]{2,})?\b',
    # 点号分隔的技术（如 .NET, ASP.NET）
    r'\b\.[A-Z][a-zA-Z]+\b',
    # 版本号模式（如 Python 3.9, Java 8）
    r'\b[A-Za-z]+\s+\d+(?:\.\d+)?\b',
]


# 常见技术栈关键词（用于上下文推断）
TECH_CONTEXT_KEYWORDS = {
    'testing': ['test', 'qa', 'quality', 'automation', 'selenium', 'playwright', 'cypress', 'appium', 'reqnroll', 'k6', 'jmeter', 'postman'],
    'framework': ['framework', 'library', 'lib', 'sdk'],
    'language': ['language', 'programming', 'code', 'develop'],
    'cloud': ['cloud', 'aws', 'azure', 'gcp', 'infrastructure'],
    'devops': ['deploy', 'ci/cd', 'pipeline', 'docker', 'kubernetes', 'jenkins'],
    'database': ['database', 'db', 'sql', 'nosql', 'query'],
    'mobile': ['mobile', 'ios', 'android', 'app', 'flutter'],
    'api': ['api', 'rest', 'graphql', 'endpoint', 'service'],
}


def extract_camel_case_terms(text: str) -> Set[str]:
    """提取驼峰命名的技术术语"""
    terms = set()
    # 匹配驼峰命名（至少两个单词）
    pattern = r'\b[A-Z][a-z]+(?:[A-Z][a-zA-Z]+)+\b'
    matches = re.findall(pattern, text)
    for match in matches:
        # 过滤掉常见的非技术词
        if len(match) > 3 and match not in ['JavaScript', 'TypeScript']:  # 这些已经在字典中
            terms.add(match)
    return terms


def extract_acronyms(text: str) -> Set[str]:
    """提取全大写缩写"""
    terms = set()
    # 匹配2-6个字母的大写缩写
    pattern = r'\b[A-Z]{2,6}\b'
    matches = re.findall(pattern, text)
    
    # 常见技术缩写白名单
    tech_acronyms = {
        'API', 'REST', 'SQL', 'NoSQL', 'JSON', 'XML', 'HTML', 'CSS', 'HTTP', 'HTTPS',
        'AWS', 'GCP', 'CI', 'CD', 'UI', 'UX', 'QA', 'SDK', 'IDE', 'CLI', 'SSH',
        'TLS', 'SSL', 'OAuth', 'JWT', 'RPC', 'gRPC', 'IoT', 'ML', 'AI', 'NLP',
        'ETL', 'BI', 'CRM', 'ERP', 'SaaS', 'PaaS', 'IaaS', 'K8s', 'YAML', 'JSON',
        'CSV', 'TSV', 'PDF', 'JIRA', 'Git', 'SVN', 'CVS', 'DNS', 'CDN', 'VPN',
        'LDAP', 'SAML', 'OIDC', 'RBAC', 'ACL', 'GDPR', 'HIPAA', 'SOC2', 'ISO',
        'TDD', 'BDD', 'DDD', 'SOLID', 'DRY', 'KISS', 'YAGNI', 'REST', 'SOAP',
        'GraphQL', 'WebSocket', 'SSE', 'CORS', 'CSRF', 'XSS', 'SQLi', 'DoS',
        'DDoS', 'WAF', 'IDS', 'IPS', 'SIEM', 'DLP', 'PKI', 'CA', 'CRL', 'OCSP',
        'JWT', 'OAuth2', 'OpenID', 'SAML2', 'LDAP', 'ActiveDirectory', 'AD',
        'DNS', 'DHCP', 'NTP', 'SMTP', 'POP3', 'IMAP', 'FTP', 'SFTP', 'SCP',
        'SSH', 'Telnet', 'RDP', 'VNC', 'RDP', 'X11', 'Wayland', 'Xorg',
        'KVM', 'Xen', 'VMware', 'Hyper-V', 'VirtualBox', 'Docker', 'Podman',
        'Kubernetes', 'OpenShift', 'Rancher', 'Mesos', 'Nomad', 'Consul',
        'Vault', 'Terraform', 'Ansible', 'Puppet', 'Chef', 'SaltStack',
        'Jenkins', 'GitLab', 'GitHub', 'Bitbucket', 'CircleCI', 'TravisCI',
        'TeamCity', 'Bamboo', 'GoCD', 'Spinnaker', 'ArgoCD', 'Flux',
        'Prometheus', 'Grafana', 'ELK', 'Splunk', 'Datadog', 'NewRelic',
        'AppDynamics', 'Dynatrace', 'Sentry', 'Rollbar', 'Bugsnag', 'Raygun',
        'LogRocket', 'FullStory', 'Hotjar', 'Mixpanel', 'Amplitude', 'Segment',
        'Snowplow', 'RudderStack', 'mParticle', 'Tealium', 'Ensighten',
        'Adobe', 'Salesforce', 'HubSpot', 'Marketo', 'Eloqua', 'Pardot',
        'Mailchimp', 'SendGrid', 'Twilio', 'Stripe', 'PayPal', 'Square',
        'Braintree', 'Adyen', 'Klarna', 'Afterpay', 'Affirm', 'Sezzle',
        'Shopify', 'WooCommerce', 'Magento', 'BigCommerce', 'Squarespace',
        'Wix', 'Webflow', 'Framer', 'Sketch', 'Figma', 'AdobeXD', 'InVision',
        'Zeplin', 'Abstract', 'Principle', 'Origami', 'Flinto', 'Proto.io',
        'Marvel', 'Balsamiq', 'Axure', 'Justinmind', 'Mockplus', 'MockFlow',
        'FluidUI', 'HotGloo', 'Pidoco', 'Wireframe', 'Mockingbird', 'Cacoo',
        'Lucidchart', 'Draw.io', 'Visio', 'OmniGraffle', 'Gliffy', 'Creately',
        'SmartDraw', 'yEd', 'Graphviz', 'PlantUML', 'Mermaid', 'D3.js',
        'Three.js', 'Babylon.js', 'A-Frame', 'React360', 'Unity', 'Unreal',
        'Godot', 'Blender', 'Maya', '3dsMax', 'Cinema4D', 'Houdini', 'ZBrush',
        'Substance', 'Marmoset', 'Toolbag', 'Quixel', 'Megascans', 'Sketchfab',
        'Poly', 'TurboSquid', 'CGTrader', '3DExport', 'Free3D', 'Clara.io',
        'Tinkercad', 'Fusion360', 'SolidWorks', 'AutoCAD', 'Inventor', 'Revit',
        'SketchUp', 'Rhino', 'Grasshopper', 'CATIA', 'NX', 'Creo', 'Pro/E',
        'SolidEdge', 'KeyCreator', 'SpaceClaim', 'ANSYS', 'Abaqus', 'COMSOL',
        'MATLAB', 'Simulink', 'LabVIEW', 'NI', 'Multisim', 'Ultiboard',
        'PADS', 'Altium', 'Eagle', 'KiCad', 'OrCAD', 'Cadence', 'Mentor',
        'Synopsys', 'Cadence', 'Mentor', 'Siemens', 'Zuken', 'Pulsonix',
        'DipTrace', 'Fritzing', 'TinyCAD', 'gEDA', 'PCB', 'SMT', 'THT',
        'BGA', 'QFP', 'QFN', 'SOP', 'SOIC', 'TSSOP', 'MSOP', 'DFN', 'LGA',
        'CSP', 'WLCSP', 'FCBGA', 'FCCSP', 'MCM', 'SiP', 'SoC', 'ASIC', 'FPGA',
        'CPLD', 'PLD', 'GAL', 'PAL', 'EPLD', 'MPU', 'MCU', 'DSP', 'GPU', 'TPU',
        'NPU', 'VPU', 'IPU', 'DPU', 'SPU', 'RPU', 'APU', 'PPU', 'EPU', 'HPU',
        'QPU', 'BPU', 'NPU', 'VPU', 'IPU', 'DPU', 'SPU', 'RPU', 'APU', 'PPU',
    }
    
    for match in matches:
        if match in tech_acronyms:
            terms.add(match)
        # 也包含一些常见的组合缩写
        elif len(match) >= 2 and len(match) <= 6:
            # 过滤掉常见的非技术词
            non_tech = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'WAY', 'USE', 'MAN', 'MEN'}
            if match not in non_tech:
                terms.add(match)
    
    return terms


def extract_dot_notation_terms(text: str) -> Set[str]:
    """提取点号分隔的技术术语（如 .NET, ASP.NET）"""
    terms = set()
    pattern = r'\b\.[A-Z][a-zA-Z]+(?:\.[A-Z][a-zA-Z]+)?\b'
    matches = re.findall(pattern, text)
    for match in matches:
        terms.add(match)
    return terms


def extract_versioned_terms(text: str) -> Set[str]:
    """提取带版本号的技术术语（如 Python 3.9, Java 8）"""
    terms = set()
    # 匹配 "技术名 版本号" 模式
    pattern = r'\b([A-Z][a-zA-Z]+)\s+(\d+(?:\.\d+)?)\b'
    matches = re.findall(pattern, text)
    for tech, version in matches:
        # 只保留技术名称，版本号作为元数据
        terms.add(tech)
    return terms


def infer_category_from_context(term: str, text: str) -> str:
    """根据上下文推断关键词类别"""
    text_lower = text.lower()
    term_lower = term.lower()
    
    # 检查测试相关
    if any(keyword in text_lower for keyword in TECH_CONTEXT_KEYWORDS['testing']):
        if any(test_word in term_lower for test_word in ['test', 'qa', 'selenium', 'playwright', 'cypress', 'appium', 'junit', 'pytest', 'jest', 'reqnroll', 'k6', 'jmeter', 'postman', 'xunit']):
            return 'testing'
    
    # 检查框架相关
    if 'framework' in text_lower or 'library' in text_lower:
        if any(fw_word in term_lower for fw_word in ['react', 'vue', 'angular', 'django', 'spring', 'express', 'flask']):
            return 'framework'
    
    # 检查云平台
    if term in ['AWS', 'Azure', 'GCP', 'Google Cloud']:
        return 'cloud'
    
    # 检查DevOps
    if term in ['Docker', 'Kubernetes', 'K8s', 'Jenkins', 'GitLab', 'GitHub', 'Pipeline']:
        return 'devops'
    
    # 检查pipeline相关
    if 'pipeline' in term_lower:
        return 'devops'
    
    # 检查数据库
    if any(db_word in term_lower for db_word in ['sql', 'database', 'db', 'mongo', 'redis', 'postgres', 'mysql']):
        return 'data'
    
    # 检查移动开发
    if term in ['iOS', 'Android', 'Flutter', 'React Native']:
        return 'platform'
    
    # 默认返回unknown，让主提取器处理
    return 'unknown'


def extract_dynamic_keywords(jd_text: str) -> List[Dict[str, any]]:
    """
    动态提取关键词（不依赖预定义字典）
    
    Returns:
        List of dicts with keys: term, category, score, count
    """
    keyword_scores = defaultdict(lambda: {"term": "", "category": "unknown", "score": 0.0, "count": 0})
    
    # 1. 提取驼峰命名术语
    camel_terms = extract_camel_case_terms(jd_text)
    for term in camel_terms:
        count = len(re.findall(r'\b' + re.escape(term) + r'\b', jd_text, re.IGNORECASE))
        category = infer_category_from_context(term, jd_text)
        keyword_scores[term.lower()] = {
            "term": term,
            "category": category,
            "score": float(count) * 1.0,
            "count": count
        }
    
    # 2. 提取缩写
    acronyms = extract_acronyms(jd_text)
    for term in acronyms:
        count = len(re.findall(r'\b' + re.escape(term) + r'\b', jd_text, re.IGNORECASE))
        category = infer_category_from_context(term, jd_text)
        keyword_scores[term.lower()] = {
            "term": term,
            "category": category,
            "score": float(count) * 1.0,
            "count": count
        }
    
    # 3. 提取点号分隔术语
    dot_terms = extract_dot_notation_terms(jd_text)
    for term in dot_terms:
        count = len(re.findall(r'\b' + re.escape(term) + r'\b', jd_text, re.IGNORECASE))
        keyword_scores[term.lower()] = {
            "term": term,
            "category": "framework",
            "score": float(count) * 1.5,  # 点号术语通常是框架，权重稍高
            "count": count
        }
    
    # 4. 提取版本化术语
    versioned_terms = extract_versioned_terms(jd_text)
    for term in versioned_terms:
        count = len(re.findall(r'\b' + re.escape(term) + r'\b', jd_text, re.IGNORECASE))
        category = infer_category_from_context(term, jd_text)
        keyword_scores[term.lower()] = {
            "term": term,
            "category": category if category != 'unknown' else 'language',
            "score": float(count) * 1.2,  # 版本化术语通常很重要
            "count": count
        }
    
    return list(keyword_scores.values())
