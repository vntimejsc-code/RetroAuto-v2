    def _add_template(self, template_name: str) -> None:
        """Add a template (multiple actions at once)."""
        template = ACTION_TEMPLATES.get(template_name)
        if not template:
            return
        
        # Get insertion index
        current_row = self.list.currentRow()
        if current_row < 0:
            current_row = self.list.count()
        
        # Add all actions from template
        actions_to_add = []
        for action_type, params in template:
            # Create action with template parameters
            action = ACTION_DEFAULTS[action_type]()
            
            # Apply template parameters
            for key, value in params.items():
                if hasattr(action, key):
                    setattr(action, key, value)
            
            actions_to_add.append(action)
        
        # Insert into list
        for i, action in enumerate(actions_to_add):
            self._actions.insert(current_row + i, action)
        
        self._refresh_list()
        self.list.setCurrentRow(current_row)
        self.actions_changed.emit(self._actions)
        
        logger.info(f"Added template: {template_name} ({len(actions_to_add)} actions)")
