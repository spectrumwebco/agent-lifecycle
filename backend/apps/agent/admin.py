from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect

from .models import AgentConfiguration, RuntimeConfiguration


@admin.register(AgentConfiguration)
class AgentConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default', 'created_at', 'updated_at')
    list_filter = ('is_default', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'config_yaml')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_default', 'load_configurations_from_files']
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_default')
        }),
        ('Configuration', {
            'fields': ('config_yaml',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def make_default(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one configuration to make default")
            return
        
        config = queryset.first()
        config.is_default = True
        config.save()
        self.message_user(request, f"Configuration '{config.name}' is now the default")
    make_default.short_description = "Make selected configuration the default"
    
    def load_configurations_from_files(self, request, queryset):
        AgentConfiguration.load_from_files()
        self.message_user(request, "Configurations loaded from files")
    load_configurations_from_files.short_description = "Load configurations from YAML files"


@admin.register(RuntimeConfiguration)
class RuntimeConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'config_type', 'is_default', 'created_at', 'updated_at')
    list_filter = ('config_type', 'is_default', 'created_at', 'updated_at')
    search_fields = ('name', 'config_json')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_default']
    fieldsets = (
        (None, {
            'fields': ('name', 'config_type', 'is_default')
        }),
        ('Configuration', {
            'fields': ('config_json',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def make_default(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one configuration to make default")
            return
        
        config = queryset.first()
        config.is_default = True
        config.save()
        self.message_user(request, f"Configuration '{config.name}' is now the default")
    make_default.short_description = "Make selected configuration the default"
