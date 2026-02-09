



































"""
=============================================================================
IntelliCV Admin Portal - Hexagonal Icon System
=============================================================================

Professional hexagonal icon system for admin portal pages.
Provides 3x3cm standardized icons with category-based styling.

Inspired by modern business intelligence interfaces with floating
hexagonal elements over blue gradients.
"""

import streamlit as st
from typing import Dict, Any

# =============================================================================
# ICON CATEGORIES AND CONFIGURATIONS
# =============================================================================

PAGE_CATEGORIES = {
    # Core Administration - Blue Gradient
    "00_Home": {
        "category": "core_admin",
        "icon": "🏠",
        "color": "#667eea",
        "gradient": "#667eea 0%, #764ba2 100%"
    },
    "01_User_Management": {
        "category": "core_admin", 
        "icon": "👥",
        "color": "#4facfe",
        "gradient": "#4facfe 0%, #00a2ff 100%"
    },
    "02_Data_Parsers": {
        "category": "core_admin",
        "icon": "📊", 
        "color": "#667eea",
        "gradient": "#667eea 0%, #764ba2 100%"
    },
    "03_System_Monitor": {
        "category": "core_admin",
        "icon": "🖥️",
        "color": "#4facfe", 
        "gradient": "#4facfe 0%, #00a2ff 100%"
    },
    
    # AI & Intelligence - Green Gradient
    "04_AI_Enrichment": {
        "category": "ai_features",
        "icon": "🧠",
        "color": "#11998e",
        "gradient": "#11998e 0%, #38ef7d 100%"
    },
    "05_Analytics": {
        "category": "ai_features",
        "icon": "📈", 
        "color": "#06beb6",
        "gradient": "#06beb6 0%, #48b1bf 100%"
    },
    "16_Market_Intelligence_Center": {
        "category": "ai_features",
        "icon": "📊",
        "color": "#11998e",
        "gradient": "#11998e 0%, #38ef7d 100%"
    },
    "17_AI_Content_Generator": {
        "category": "ai_features", 
        "icon": "✨",
        "color": "#06beb6",
        "gradient": "#06beb6 0%, #48b1bf 100%"
    },
    "18_Web_Company_Intelligence": {
        "category": "ai_features",
        "icon": "🌐",
        "color": "#11998e", 
        "gradient": "#11998e 0%, #38ef7d 100%"
    },
    
    # System Operations - Orange Gradient  
    "06_Compliance_Audit": {
        "category": "system_ops",
        "icon": "🛡️",
        "color": "#f093fb",
        "gradient": "#f093fb 0%, #f5576c 100%"
    },
    "07_API_Integration": {
        "category": "system_ops",
        "icon": "🔧",
        "color": "#ff9a9e", 
        "gradient": "#ff9a9e 0%, #fecfef 100%"
    },
    "08_Contact_Communication": {
        "category": "system_ops",
        "icon": "📧",
        "color": "#f093fb",
        "gradient": "#f093fb 0%, #f5576c 100%"
    },
    "09_Batch_Processing": {
        "category": "system_ops",
        "icon": "⚡",
        "color": "#ff9a9e",
        "gradient": "#ff9a9e 0%, #fecfef 100%"
    },
    "10_Advanced_Logging": {
        "category": "system_ops", 
        "icon": "📋",
        "color": "#f093fb",
        "gradient": "#f093fb 0%, #f5576c 100%"
    },
    "11_Advanced_Settings": {
        "category": "system_ops",
        "icon": "⚙️",
        "color": "#ff9a9e",
        "gradient": "#ff9a9e 0%, #fecfef 100%"
    },
    
    # Specialized Tools - Purple Gradient
    "12_Competitive_Intelligence": {
        "category": "security_tools",
        "icon": "🎯", 
        "color": "#a18cd1",
        "gradient": "#a18cd1 0%, #fbc2eb 100%"
    },
    "13_Enhanced_Glossary": {
        "category": "security_tools",
        "icon": "📚",
        "color": "#667eea",
        "gradient": "#667eea 0%, #764ba2 100%"
    },
    "14_System_Snapshot": {
        "category": "security_tools",
        "icon": "📸",
        "color": "#a18cd1",
        "gradient": "#a18cd1 0%, #fbc2eb 100%"
    },
    "15_Legacy_Utilities": {
        "category": "security_tools", 
        "icon": "🔧",
        "color": "#667eea",
        "gradient": "#667eea 0%, #764ba2 100%"
    },
    "19_Backup_Management": {
        "category": "security_tools",
        "icon": "💾",
        "color": "#a18cd1",
        "gradient": "#a18cd1 0%, #fbc2eb 100%"
    }
}

# =============================================================================
# ICON RENDERING FUNCTIONS
# =============================================================================

def get_page_category(page_name: str) -> Dict[str, Any]:
    """Get category information for a page"""
    return PAGE_CATEGORIES.get(page_name, {
        "category": "core_admin",
        "icon": "⬢", 
        "color": "#667eea",
        "gradient": "#667eea 0%, #764ba2 100%"
    })

def render_page_icon(page_name: str, position: str = "top-right") -> None:
    """
    Render a 3x3cm hexagonal page icon
    
    Args:
        page_name: Name of the page (e.g., "01_User_Management")
        position: Position of the icon ("top-right", "top-left", etc.)
    """
    page_info = get_page_category(page_name)
    
    # Calculate 3x3cm in pixels (assuming 96 DPI)
    # 3cm = 3 * 37.795275591 ≈ 113.386 pixels
    icon_size = "113px"
    
    # Position styles
    position_styles = {
        "top-right": "position: fixed; top: 20px; right: 20px; z-index: 1000;",
        "top-left": "position: fixed; top: 20px; left: 20px; z-index: 1000;",
        "inline": "display: inline-block; margin: 10px;"
    }
    
    # Render the hexagonal icon
    st.markdown(f"""
    <div style="{position_styles.get(position, position_styles['top-right'])}">
        <div style="
            width: {icon_size};
            height: {icon_size};
            background: linear-gradient(135deg, {page_info['gradient']});
            clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        " 
        onmouseover="this.style.transform='scale(1.1) rotate(5deg)'; this.style.boxShadow='0 12px 40px rgba(0,0,0,0.3)';"
        onmouseout="this.style.transform='scale(1) rotate(0deg)'; this.style.boxShadow='0 8px 32px rgba(0,0,0,0.2)';">
            
            <!-- Hexagonal pattern overlay -->
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                opacity: 0.1;
                font-size: 40px;
                color: white;
                line-height: 0.6;
            ">⬢<br>⬡<br>⬢</div>
            
            <!-- Main icon -->
            <div style="
                font-size: 36px;
                color: white;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                position: relative;
                z-index: 2;
            ">{page_info['icon']}</div>
        </div>
        
        <!-- Tooltip -->
        <div style="
            position: absolute;
            bottom: -35px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        " class="icon-tooltip">{page_name.replace('_', ' ').title()}</div>
    </div>
    
    <style>
    .icon-tooltip {{
        opacity: 0;
    }}
    div:hover .icon-tooltip {{
        opacity: 1;
    }}
    </style>
    """, unsafe_allow_html=True)

def render_icon_grid(pages: list, columns: int = 4) -> None:
    """
    Render a grid of hexagonal icons for multiple pages
    
    Args:
        pages: List of page names
        columns: Number of columns in the grid
    """
    st.markdown("""
    <style>
    .icon-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 20px;
        padding: 20px;
        justify-items: center;
    }
    .icon-grid-item {
        text-align: center;
    }
    .icon-title {
        margin-top: 10px;
        font-size: 12px;
        color: #666;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="icon-grid">', unsafe_allow_html=True)
    
    for page in pages:
        page_info = get_page_category(page)
        
        st.markdown(f"""
        <div class="icon-grid-item">
            <div style="
                width: 113px;
                height: 113px;
                background: linear-gradient(135deg, {page_info['gradient']});
                clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
                cursor: pointer;
                margin: 0 auto;
                position: relative;
                overflow: hidden;
            " 
            onmouseover="this.style.transform='scale(1.1) rotate(5deg)'; this.style.boxShadow='0 12px 40px rgba(0,0,0,0.3)';"
            onmouseout="this.style.transform='scale(1) rotate(0deg)'; this.style.boxShadow='0 8px 32px rgba(0,0,0,0.2)';">
                
                <!-- Hexagonal pattern overlay -->
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    opacity: 0.1;
                    font-size: 30px;
                    color: white;
                    line-height: 0.6;
                ">⬢<br>⬡<br>⬢</div>
                
                <!-- Main icon -->
                <div style="
                    font-size: 36px;
                    color: white;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    position: relative;
                    z-index: 2;
                ">{page_info['icon']}</div>
            </div>
            
            <div class="icon-title">{page.replace('_', ' ').title()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def inject_icon_css() -> None:
    """Inject CSS for enhanced icon animations and effects"""
    st.markdown("""
    <style>
    @keyframes hexFloat {
        0% { transform: translateY(0px) rotate(0deg); }
        25% { transform: translateY(-10px) rotate(2deg); }
        50% { transform: translateY(-5px) rotate(0deg); }
        75% { transform: translateY(-15px) rotate(-2deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    
    .floating-hex {
        animation: hexFloat 6s ease-in-out infinite;
    }
    
    .hex-glow {
        filter: drop-shadow(0 0 10px rgba(102, 126, 234, 0.5));
    }
    
    .page-icon-container {
        position: relative;
    }
    
    .page-icon-container::before {
        content: '';
        position: absolute;
        top: -10px;
        left: -10px;
        right: -10px;
        bottom: -10px;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
        border-radius: 50%;
        z-index: -1;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .page-icon-container:hover::before {
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_admin_pages() -> list:
    """Get list of all admin pages"""
    return [f"{i:02d}_Page" for i in range(20)] + list(PAGE_CATEGORIES.keys())

def render_category_legend() -> None:
    """Render a legend showing different icon categories"""
    st.markdown("### 🎨 Icon Categories")
    
    categories = {
        "Core Administration": {"color": "#4facfe", "gradient": "#4facfe 0%, #00a2ff 100%", "icon": "👥"},
        "AI & Intelligence": {"color": "#11998e", "gradient": "#11998e 0%, #38ef7d 100%", "icon": "🧠"},
        "System Operations": {"color": "#f093fb", "gradient": "#f093fb 0%, #f5576c 100%", "icon": "⚙️"},
        "Security & Tools": {"color": "#667eea", "gradient": "#667eea 0%, #764ba2 100%", "icon": "🛡️"}
    }
    
    cols = st.columns(len(categories))
    for i, (cat_name, cat_info) in enumerate(categories.items()):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <div style="
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, {cat_info['gradient']});
                    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 10px;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
                ">
                    <span style="font-size: 24px; color: white;">{cat_info['icon']}</span>
                </div>
                <div style="font-size: 12px; color: #666; font-weight: 500;">{cat_name}</div>
            </div>
            """, unsafe_allow_html=True)
