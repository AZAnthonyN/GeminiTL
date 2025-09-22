"""
Multi-provider configuration dialog.

This module provides a GUI for configuring multiple AI providers.
"""

import os
import wx
import json
from typing import Dict, Any
from config.multi_provider_config import config_manager
from ai_providers.provider_factory import ProviderFactory


class MultiProviderConfigDialog(wx.Dialog):
    """Enhanced configuration dialog for multiple AI providers."""

    def __init__(self, parent):
        super().__init__(parent, title="AI Provider Configuration", size=(700, 600))
        
        self.config_manager = config_manager
        self.provider_panels = {}
        
        self.create_ui()
        self.load_values()

    def create_ui(self):
        """Create the user interface."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(panel, label="AI Provider Configuration")
        title_font = title.GetFont()
        title_font.SetPointSize(14)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)

        # Create notebook for different providers
        self.notebook = wx.Notebook(panel)
        
        # General settings tab
        self.create_general_tab()
        
        # Provider-specific tabs
        self.create_provider_tabs()
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()

        save_btn = wx.Button(panel, wx.ID_OK, "Save")
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sizer.AddButton(save_btn)

        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.AddButton(cancel_btn)

        test_btn = wx.Button(panel, label="Test Providers")
        test_btn.Bind(wx.EVT_BUTTON, self.on_test_providers)
        btn_sizer.Add(test_btn, 0, wx.ALL, 5)

        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 10)

        panel.SetSizer(main_sizer)

    def create_general_tab(self):
        """Create the general settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Default provider selection
        provider_sizer = wx.BoxSizer(wx.HORIZONTAL)
        provider_sizer.Add(wx.StaticText(panel, label="Default Provider:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        self.default_provider_choice = wx.Choice(panel, choices=ProviderFactory.get_provider_names())
        provider_sizer.Add(self.default_provider_choice, 1, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(provider_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Fallback order
        fallback_box = wx.StaticBox(panel, label="Fallback Provider Order")
        fallback_sizer = wx.StaticBoxSizer(fallback_box, wx.VERTICAL)
        
        self.fallback_list = wx.ListBox(panel, style=wx.LB_SINGLE)
        fallback_sizer.Add(self.fallback_list, 1, wx.EXPAND | wx.ALL, 5)
        
        fallback_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.move_up_btn = wx.Button(panel, label="Move Up")
        self.move_up_btn.Bind(wx.EVT_BUTTON, self.on_move_up)
        fallback_btn_sizer.Add(self.move_up_btn, 0, wx.ALL, 2)
        
        self.move_down_btn = wx.Button(panel, label="Move Down")
        self.move_down_btn.Bind(wx.EVT_BUTTON, self.on_move_down)
        fallback_btn_sizer.Add(self.move_down_btn, 0, wx.ALL, 2)
        
        fallback_sizer.Add(fallback_btn_sizer, 0, wx.CENTER)
        sizer.Add(fallback_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # Retry settings
        retry_box = wx.StaticBox(panel, label="Retry Settings")
        retry_sizer = wx.StaticBoxSizer(retry_box, wx.VERTICAL)
        
        retry_grid = wx.FlexGridSizer(3, 2, 5, 5)
        retry_grid.AddGrowableCol(1)
        
        retry_grid.Add(wx.StaticText(panel, label="Max Retries:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.max_retries_ctrl = wx.SpinCtrl(panel, min=1, max=10, initial=3)
        retry_grid.Add(self.max_retries_ctrl, 1, wx.EXPAND)
        
        retry_grid.Add(wx.StaticText(panel, label="Base Delay (seconds):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.base_delay_ctrl = wx.SpinCtrlDouble(panel, min=0.1, max=10.0, initial=1.0, inc=0.1)
        retry_grid.Add(self.base_delay_ctrl, 1, wx.EXPAND)
        
        self.exponential_backoff_cb = wx.CheckBox(panel, label="Use Exponential Backoff")
        retry_grid.Add(self.exponential_backoff_cb, 0, wx.ALIGN_CENTER_VERTICAL)
        retry_grid.Add(wx.StaticText(panel, label=""), 0)  # Empty cell
        
        retry_sizer.Add(retry_grid, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(retry_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "General")

    def create_provider_tabs(self):
        """Create tabs for each provider."""
        available_providers = ProviderFactory.get_provider_names()
        
        for provider_name in available_providers:
            panel = wx.Panel(self.notebook)
            self.provider_panels[provider_name] = panel
            
            sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Enable/disable checkbox
            enable_cb = wx.CheckBox(panel, label=f"Enable {provider_name.title()}")
            setattr(self, f"{provider_name}_enabled_cb", enable_cb)
            sizer.Add(enable_cb, 0, wx.ALL, 10)
            
            # Provider-specific configuration
            self.create_provider_config_ui(panel, sizer, provider_name)
            
            panel.SetSizer(sizer)
            self.notebook.AddPage(panel, provider_name.title())

    def create_provider_config_ui(self, panel, sizer, provider_name):
        """Create provider-specific configuration UI."""
        # Get the provider schema
        try:
            provider_type = getattr(__import__('ai_providers.base_provider', fromlist=['ProviderType']), 'ProviderType')(provider_name)
            provider = ProviderFactory.create_provider(provider_type, {})
            if not provider:
                return
                
            schema = provider.get_config_schema()
            properties = schema.get("properties", {})
            
            config_box = wx.StaticBox(panel, label="Configuration")
            config_sizer = wx.StaticBoxSizer(config_box, wx.VERTICAL)
            
            form_sizer = wx.FlexGridSizer(len(properties), 2, 5, 5)
            form_sizer.AddGrowableCol(1)
            
            for field_name, field_info in properties.items():
                label = wx.StaticText(panel, label=f"{field_name.replace('_', ' ').title()}:")
                form_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
                
                field_type = field_info.get("type", "string")
                
                if field_name == "model" and "enum" in field_info:
                    # Model selection dropdown
                    ctrl = wx.Choice(panel, choices=field_info["enum"])
                    if "default" in field_info:
                        default_idx = field_info["enum"].index(field_info["default"])
                        ctrl.SetSelection(default_idx)
                elif field_type == "number":
                    # Numeric input with validation
                    min_val = field_info.get("minimum", 0.0)
                    max_val = field_info.get("maximum", 100.0)
                    default_val = field_info.get("default", min_val)
                    ctrl = wx.SpinCtrlDouble(panel, min=min_val, max=max_val, initial=default_val, inc=0.1)
                elif field_type == "integer":
                    # Integer input
                    min_val = field_info.get("minimum", 1)
                    max_val = field_info.get("maximum", 1000)
                    default_val = field_info.get("default", min_val)
                    ctrl = wx.SpinCtrl(panel, min=min_val, max=max_val, initial=default_val)
                else:
                    # Text input
                    style = wx.TE_PASSWORD if "key" in field_name.lower() else 0
                    ctrl = wx.TextCtrl(panel, style=style)
                    if "default" in field_info:
                        ctrl.SetValue(str(field_info["default"]))
                
                # Add help text if available
                if "description" in field_info:
                    ctrl.SetToolTip(field_info["description"])
                
                form_sizer.Add(ctrl, 1, wx.EXPAND)
                
                # Store reference to the control
                setattr(self, f"{provider_name}_{field_name}_ctrl", ctrl)
            
            config_sizer.Add(form_sizer, 1, wx.EXPAND | wx.ALL, 5)
            sizer.Add(config_sizer, 1, wx.EXPAND | wx.ALL, 10)
            
        except Exception as e:
            error_text = wx.StaticText(panel, label=f"Error loading {provider_name} configuration: {e}")
            sizer.Add(error_text, 0, wx.ALL, 10)

    def load_values(self):
        """Load current values into the form."""
        # Load general settings
        default_provider = self.config_manager.get_default_provider()
        provider_names = ProviderFactory.get_provider_names()
        if default_provider in provider_names:
            self.default_provider_choice.SetSelection(provider_names.index(default_provider))
        
        # Load fallback order
        fallback_providers = self.config_manager.get_fallback_providers()
        self.fallback_list.Set(fallback_providers)
        
        # Load retry settings
        retry_settings = self.config_manager.get_retry_settings()
        self.max_retries_ctrl.SetValue(retry_settings.get("max_retries", 3))
        self.base_delay_ctrl.SetValue(retry_settings.get("base_delay", 1.0))
        self.exponential_backoff_cb.SetValue(retry_settings.get("exponential_backoff", True))
        
        # Load provider-specific settings
        for provider_name in ProviderFactory.get_provider_names():
            self.load_provider_values(provider_name)

    def load_provider_values(self, provider_name):
        """Load values for a specific provider."""
        config = self.config_manager.get_provider_config(provider_name)
        
        # Load enabled state
        enabled_cb = getattr(self, f"{provider_name}_enabled_cb", None)
        if enabled_cb:
            enabled_cb.SetValue(config.get("enabled", False))
        
        # Load other configuration values
        for key, value in config.items():
            if key == "enabled":
                continue
            ctrl = getattr(self, f"{provider_name}_{key}_ctrl", None)
            if ctrl:
                if isinstance(ctrl, wx.Choice):
                    choices = ctrl.GetStrings()
                    if str(value) in choices:
                        ctrl.SetSelection(choices.index(str(value)))
                elif isinstance(ctrl, (wx.SpinCtrl, wx.SpinCtrlDouble)):
                    ctrl.SetValue(float(value) if isinstance(value, (int, float)) else 0)
                else:
                    ctrl.SetValue(str(value))

    def on_move_up(self, event):
        """Move selected fallback provider up."""
        selection = self.fallback_list.GetSelection()
        if selection > 0:
            items = list(self.fallback_list.GetStrings())
            items[selection], items[selection - 1] = items[selection - 1], items[selection]
            self.fallback_list.Set(items)
            self.fallback_list.SetSelection(selection - 1)

    def on_move_down(self, event):
        """Move selected fallback provider down."""
        selection = self.fallback_list.GetSelection()
        items = list(self.fallback_list.GetStrings())
        if 0 <= selection < len(items) - 1:
            items[selection], items[selection + 1] = items[selection + 1], items[selection]
            self.fallback_list.Set(items)
            self.fallback_list.SetSelection(selection + 1)

    def on_test_providers(self, event):
        """Test all enabled providers."""
        # This would implement provider testing
        wx.MessageBox("Provider testing not yet implemented.", "Info", wx.OK | wx.ICON_INFORMATION)

    def on_save(self, event):
        """Save the configuration."""
        try:
            # Save general settings
            provider_names = ProviderFactory.get_provider_names()
            default_idx = self.default_provider_choice.GetSelection()
            if default_idx >= 0:
                self.config_manager.set_default_provider(provider_names[default_idx])
            
            # Save fallback order
            fallback_order = list(self.fallback_list.GetStrings())
            self.config_manager.set_fallback_providers(fallback_order)
            
            # Save retry settings
            retry_settings = {
                "max_retries": self.max_retries_ctrl.GetValue(),
                "base_delay": self.base_delay_ctrl.GetValue(),
                "exponential_backoff": self.exponential_backoff_cb.GetValue()
            }
            self.config_manager.set_retry_settings(retry_settings)
            
            # Save provider-specific settings
            for provider_name in ProviderFactory.get_provider_names():
                self.save_provider_config(provider_name)
            
            wx.MessageBox("Configuration saved successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
            self.EndModal(wx.ID_OK)
            
        except Exception as e:
            wx.MessageBox(f"Error saving configuration: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def save_provider_config(self, provider_name):
        """Save configuration for a specific provider."""
        config = {}
        
        # Save enabled state
        enabled_cb = getattr(self, f"{provider_name}_enabled_cb", None)
        if enabled_cb:
            config["enabled"] = enabled_cb.GetValue()
        
        # Save other configuration values
        try:
            provider_type = getattr(__import__('ai_providers.base_provider', fromlist=['ProviderType']), 'ProviderType')(provider_name)
            provider = ProviderFactory.create_provider(provider_type, {})
            if provider:
                schema = provider.get_config_schema()
                properties = schema.get("properties", {})
                
                for field_name in properties.keys():
                    ctrl = getattr(self, f"{provider_name}_{field_name}_ctrl", None)
                    if ctrl:
                        if isinstance(ctrl, wx.Choice):
                            selection = ctrl.GetSelection()
                            if selection >= 0:
                                config[field_name] = ctrl.GetString(selection)
                        elif isinstance(ctrl, (wx.SpinCtrl, wx.SpinCtrlDouble)):
                            config[field_name] = ctrl.GetValue()
                        else:
                            config[field_name] = ctrl.GetValue()
        except Exception as e:
            print(f"Error saving {provider_name} config: {e}")
        
        self.config_manager.set_provider_config(provider_name, config)
