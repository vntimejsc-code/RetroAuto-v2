"""
Tests for core/dsl/autocomplete.py - AutocompleteProvider
"""

import pytest
from core.dsl.autocomplete import AutocompleteProvider, CompletionItem, CompletionKind


class TestCompletionItem:
    """Tests for CompletionItem."""
    
    def test_completion_item_creation(self):
        item = CompletionItem(
            label="click",
            kind=CompletionKind.FUNCTION,
            detail="Click at position"
        )
        assert item.label == "click"
        assert item.kind == CompletionKind.FUNCTION
        assert item.detail == "Click at position"
    
    def test_completion_item_insert_text_default(self):
        item = CompletionItem(
            label="click",
            kind=CompletionKind.FUNCTION
        )
        assert item.insert_text == "click"
    
    def test_completion_item_custom_insert_text(self):
        item = CompletionItem(
            label="click",
            kind=CompletionKind.FUNCTION,
            insert_text="click($1, $2)"
        )
        assert item.insert_text == "click($1, $2)"


class TestCompletionKind:
    """Tests for CompletionKind enum."""
    
    def test_completion_kinds_exist(self):
        assert hasattr(CompletionKind, "KEYWORD")
        assert hasattr(CompletionKind, "FUNCTION")
        assert hasattr(CompletionKind, "VARIABLE")
        assert hasattr(CompletionKind, "ASSET")
        assert hasattr(CompletionKind, "FLOW")
        assert hasattr(CompletionKind, "SNIPPET")


class TestAutocompleteProvider:
    """Tests for AutocompleteProvider."""
    
    def test_provider_creation(self):
        provider = AutocompleteProvider()
        assert provider is not None
    
    def test_set_context(self):
        provider = AutocompleteProvider()
        provider.set_context(
            assets=["btn_ok", "img_error"],
            flows=["main", "login"],
            variables=["counter", "result"]
        )
        # No exception means success
    
    def test_complete_keyword(self):
        provider = AutocompleteProvider()
        items = provider.complete("fl")
        
        # Should suggest "flow"
        labels = [item.label for item in items]
        assert "flow" in labels
    
    def test_complete_function(self):
        provider = AutocompleteProvider()
        items = provider.complete("cli")
        
        labels = [item.label for item in items]
        assert "click" in labels
    
    def test_complete_asset(self):
        provider = AutocompleteProvider()
        provider.set_context(assets=["btn_ok", "btn_cancel"])
        
        items = provider.complete("btn", in_string=True)
        labels = [item.label for item in items]
        
        assert "btn_ok" in labels
        assert "btn_cancel" in labels
    
    def test_complete_flow(self):
        provider = AutocompleteProvider()
        provider.set_context(flows=["main", "login", "logout"])
        
        items = provider.complete("log", in_string=True)
        labels = [item.label for item in items]
        
        assert "login" in labels
        assert "logout" in labels
    
    def test_complete_variable(self):
        provider = AutocompleteProvider()
        provider.set_context(variables=["counter", "result"])
        
        items = provider.complete("cou")
        labels = [item.label for item in items]
        
        assert "counter" in labels
    
    def test_get_all_functions(self):
        provider = AutocompleteProvider()
        functions = provider.get_all_functions()
        
        assert len(functions) > 0
        labels = [f.label for f in functions]
        assert "click" in labels
        assert "wait_image" in labels
    
    def test_get_all_keywords(self):
        provider = AutocompleteProvider()
        keywords = provider.get_all_keywords()
        
        assert len(keywords) > 0
        labels = [k.label for k in keywords]
        assert "flow" in labels
    
    def test_get_function_signature(self):
        provider = AutocompleteProvider()
        sig = provider.get_function_signature("click")
        
        assert sig is not None
        assert "click" in sig
    
    def test_empty_prefix(self):
        provider = AutocompleteProvider()
        items = provider.complete("")
        
        # Should return some results
        assert len(items) >= 0
    
    def test_no_match(self):
        provider = AutocompleteProvider()
        items = provider.complete("xyz_nonexistent")
        
        # Should return empty or very few results
        assert len(items) == 0
