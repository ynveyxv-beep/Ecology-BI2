from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import copy
import json


@dataclass
class HistoryState:
    """Состояние дашборда для истории"""
    dashboard_data: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: __import__('time').time())


class HistoryManager:
    """Управление историей действий (Undo/Redo)"""
    
    MAX_HISTORY = 50
    
    def __init__(self):
        self.undo_stack: List[HistoryState] = []
        self.redo_stack: List[HistoryState] = []
        self._is_restoring = False
    
    def push_state(self, dashboard_data: Dict[str, Any]):
        """Сохраняет состояние в историю"""
        if self._is_restoring:
            return
        
        state = HistoryState(
            dashboard_data=copy.deepcopy(dashboard_data)
        )
        
        self.undo_stack.append(state)
        
        if len(self.undo_stack) > self.MAX_HISTORY:
            self.undo_stack.pop(0)
        
        self.redo_stack.clear()
    
    def undo(self, current_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Отменяет последнее действие"""
        if len(self.undo_stack) <= 1:
            return None
        
        self.redo_stack.append(HistoryState(
            dashboard_data=copy.deepcopy(current_data)
        ))
        
        self._is_restoring = True
        result = copy.deepcopy(self.undo_stack[-2].dashboard_data)
        self._is_restoring = False
        
        return result
    
    def redo(self, current_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Повторяет отменённое действие"""
        if not self.redo_stack:
            return None
        
        self.undo_stack.append(HistoryState(
            dashboard_data=copy.deepcopy(current_data)
        ))
        
        self._is_restoring = True
        result = copy.deepcopy(self.redo_stack.pop().dashboard_data)
        self._is_restoring = False
        
        return result
    
    def can_undo(self) -> bool:
        """Проверяет, есть ли действия для отмены"""
        return len(self.undo_stack) > 1
    
    def can_redo(self) -> bool:
        """Проверяет, есть ли действия для повтора"""
        return len(self.redo_stack) > 0
    
    def clear(self):
        """Очищает историю"""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def get_undo_count(self) -> int:
        """Возвращает количество действий в Undo"""
        return len(self.undo_stack) - 1 if self.undo_stack else 0
    
    def get_redo_count(self) -> int:
        """Возвращает количество действий в Redo"""
        return len(self.redo_stack)