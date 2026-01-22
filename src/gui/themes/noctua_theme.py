"""
Noctua-inspired sandy/brown color theme.

Color palette inspired by Noctua branding:
- Sandy beige/tan (sand dunes)
- Dark brown (chocolate)
- Warm neutrals
"""

import dearpygui.dearpygui as dpg


def create_noctua_theme():
    """
    Create and return Noctua-inspired theme.

    Returns:
        Theme ID for DearPyGUI
    """
    with dpg.theme() as noctua_theme:
        with dpg.theme_component(dpg.mvAll):
            # Background colors - sandy/beige tones
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (45, 38, 32), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (50, 42, 35), category=dpg.mvThemeCat_Core)  # Lighter brown for panels
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (50, 42, 35), category=dpg.mvThemeCat_Core)

            # Frame backgrounds - darker brown
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (35, 30, 25), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (60, 50, 42), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (70, 58, 48), category=dpg.mvThemeCat_Core)

            # Title bar - sandy beige
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (80, 65, 50), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (100, 82, 62), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (60, 50, 40), category=dpg.mvThemeCat_Core)

            # Buttons - warm brown
            dpg.add_theme_color(dpg.mvThemeCol_Button, (90, 72, 55), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (110, 88, 67), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (130, 104, 79), category=dpg.mvThemeCat_Core)

            # Headers - sandy
            dpg.add_theme_color(dpg.mvThemeCol_Header, (70, 58, 46), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (90, 74, 58), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (100, 82, 64), category=dpg.mvThemeCat_Core)

            # Tab colors - sandy with brown accents
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (70, 58, 46), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (100, 82, 64), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (120, 98, 76), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (60, 50, 40), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (80, 66, 52), category=dpg.mvThemeCat_Core)

            # Text - light sandy/cream for contrast
            dpg.add_theme_color(dpg.mvThemeCol_Text, (230, 220, 200), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (140, 130, 115), category=dpg.mvThemeCat_Core)

            # Borders - subtle brown
            dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 50, 40), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (20, 18, 15), category=dpg.mvThemeCat_Core)

            # Scrollbar - dark brown
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (35, 30, 25), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (70, 58, 46), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (90, 74, 58), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (110, 90, 70), category=dpg.mvThemeCat_Core)

            # Checkboxes - sandy with accent
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (180, 145, 110), category=dpg.mvThemeCat_Core)

            # Slider/grab - warm brown
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (100, 82, 62), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (130, 106, 80), category=dpg.mvThemeCat_Core)

            # Separator - subtle
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (60, 50, 40), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, (80, 66, 52), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, (100, 82, 64), category=dpg.mvThemeCat_Core)

            # Resize grip - brown
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, (70, 58, 46), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, (90, 74, 58), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, (110, 90, 70), category=dpg.mvThemeCat_Core)

            # Table colors - dark brown background
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (55, 46, 37), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, (65, 54, 43), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (50, 42, 34), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (35, 30, 25), category=dpg.mvThemeCat_Core)  # Dark brown
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (40, 34, 28), category=dpg.mvThemeCat_Core)  # Slightly lighter

            # Menu bar - sandy
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (60, 50, 40), category=dpg.mvThemeCat_Core)

            # Rounded corners for softer look
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 4, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 3, category=dpg.mvThemeCat_Core)

        # Disabled state styling for buttons and other controls
        with dpg.theme_component(dpg.mvButton, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (65, 54, 43), category=dpg.mvThemeCat_Core)  # Lighter muted brown (visible against panel)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (65, 54, 43), category=dpg.mvThemeCat_Core)  # Same as normal - no hover
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (65, 54, 43), category=dpg.mvThemeCat_Core)  # Same as normal - no click effect
            dpg.add_theme_color(dpg.mvThemeCol_Text, (120, 110, 95), category=dpg.mvThemeCat_Core)  # Lighter muted sandy text

        # Disabled state for input fields
        with dpg.theme_component(dpg.mvInputText, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 34, 28), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (100, 90, 80), category=dpg.mvThemeCat_Core)

    return noctua_theme


def create_dark_container_theme():
    """
    Create theme for dark containers (console, tables).

    Use with dpg.bind_item_theme() on specific widgets.

    Returns:
        Theme ID for DearPyGUI
    """
    with dpg.theme() as dark_theme:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (35, 30, 25), category=dpg.mvThemeCat_Core)

    return dark_theme
