import dearpygui.dearpygui as dpg


class AppTheme:
    """Global theme system for MCAT application."""
    
    @staticmethod
    def create_global_theme():
        """Create and apply the global application theme."""
        with dpg.theme() as global_theme:
            
            # Core UI components
            with dpg.theme_component(dpg.mvAll):
                # Colors
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [35, 35, 35], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, [40, 40, 40], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [50, 50, 50], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [60, 60, 60], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [70, 70, 70], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, [60, 60, 60], category=dpg.mvThemeCat_Core)
                
                # Reduced padding and spacing
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 4, 3, category=dpg.mvThemeCat_Core)  # Reduced vertical spacing
                dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 4, 2, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3, category=dpg.mvThemeCat_Core)
            
            # Button specific styling
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, [80, 80, 80], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [90, 90, 90], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [100, 100, 100], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6, category=dpg.mvThemeCat_Core)
            
            # Tab specific styling
            with dpg.theme_component(dpg.mvTab):
                dpg.add_theme_color(dpg.mvThemeCol_Tab, [45, 45, 45], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [55, 55, 55], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, [65, 65, 65], category=dpg.mvThemeCat_Core)
            
            # Combo box specific styling
            with dpg.theme_component(dpg.mvCombo):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [45, 45, 45], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [55, 55, 55], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [65, 65, 65], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6, category=dpg.mvThemeCat_Core)
            
            # Input text specific styling
            with dpg.theme_component(dpg.mvInputText):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [45, 45, 45], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [55, 55, 55], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [65, 65, 65], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6, category=dpg.mvThemeCat_Core)
        
        return global_theme
    
    @staticmethod
    def create_disabled_theme():
        """Create theme for disabled items."""
        with dpg.theme() as disabled_theme:
            with dpg.theme_component(dpg.mvAll, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_Text, [80, 80, 80], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [25, 25, 25], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, [30, 30, 30], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [30, 30, 30], category=dpg.mvThemeCat_Core)  # Same as normal to prevent hover
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [30, 30, 30], category=dpg.mvThemeCat_Core)   # Same as normal to prevent active
        
        return disabled_theme
    
    @staticmethod
    def create_disabled_button_theme():
        """Create specific disabled button theme."""
        with dpg.theme() as disabled_button_theme:
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_Text, [80, 80, 80], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, [30, 30, 30], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [30, 30, 30], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [30, 30, 30], category=dpg.mvThemeCat_Core)
        
        return disabled_button_theme
    
    @staticmethod
    def apply_themes():
        """Apply all themes to the application."""
        global_theme = AppTheme.create_global_theme()
        disabled_theme = AppTheme.create_disabled_theme()
        disabled_button_theme = AppTheme.create_disabled_button_theme()
        
        # Apply global theme
        dpg.bind_theme(global_theme)
        dpg.bind_theme(disabled_theme)
        dpg.bind_theme(disabled_button_theme)
        
        return global_theme, disabled_theme, disabled_button_theme