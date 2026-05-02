# Path: usekit.tools.keymemory.base.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# -----------------------------------------------------------------------------------------------

"""
KeyMemory Base Module

Core KeyMemory class for .km format handling
"""

from pathlib import Path
from typing import Dict, Optional, Any
from usekit.tools.keymemory.parser import KMParser


class KeyMemory:
    """
    KeyMemory class for managing .km format anchors
    
    Usage:
        km = KeyMemory.load("paths.km")
        path = km.resolve("@MODEL_CLS")
        
        # Dict-like access
        base = km["@BASE"]
        src = km.get("@SRC", default="/default/src")
    """
    
    def __init__(self, anchors: Optional[Dict[str, str]] = None):
        """
        Initialize KeyMemory
        
        Args:
            anchors: Dictionary of resolved anchors
        """
        self._anchors = anchors or {}
        
    @classmethod
    def load(cls, km_path: str | Path) -> 'KeyMemory':
        """
        Load KeyMemory from .km file
        
        Args:
            km_path: Path to .km file
            
        Returns:
            KeyMemory instance with loaded anchors
            
        Example:
            km = KeyMemory.load("config/paths.km")
        """
        anchors = KMParser.parse_file(km_path)
        return cls(anchors)
    
    def resolve(self, anchor_name: str) -> Path:
        """
        Resolve anchor to Path object
        
        Args:
            anchor_name: Anchor name (e.g., '@BASE', '@MODEL_CLS')
            
        Returns:
            Path object for the resolved anchor
            
        Raises:
            KeyError: If anchor not found
            
        Example:
            path = km.resolve("@BASE")
        """
        if anchor_name not in self._anchors:
            available = ', '.join(self._anchors.keys())
            raise KeyError(
                f"Anchor '{anchor_name}' not found. "
                f"Available: {available}"
            )
        
        return Path(self._anchors[anchor_name])
    
    def get(self, key: str, default: Any = None) -> Optional[str]:
        """
        Dict-like get with default
        
        Args:
            key: Anchor name
            default: Default value if key not found
            
        Returns:
            Anchor value or default
            
        Example:
            src = km.get("@SRC", "/default/src")
        """
        return self._anchors.get(key, default)
    
    def __getitem__(self, key: str) -> str:
        """
        Dict-like access: km['@BASE']
        
        Args:
            key: Anchor name
            
        Returns:
            Anchor value
            
        Raises:
            KeyError: If anchor not found
        """
        if key not in self._anchors:
            available = ', '.join(self._anchors.keys())
            raise KeyError(
                f"Anchor '{key}' not found. "
                f"Available: {available}"
            )
        return self._anchors[key]
    
    def __contains__(self, key: str) -> bool:
        """
        Check if anchor exists: '@BASE' in km
        
        Args:
            key: Anchor name
            
        Returns:
            True if anchor exists
        """
        return key in self._anchors
    
    def __len__(self) -> int:
        """
        Number of anchors: len(km)
        
        Returns:
            Number of loaded anchors
        """
        return len(self._anchors)
    
    def __repr__(self) -> str:
        """
        String representation
        
        Returns:
            String showing number of anchors
        """
        return f"<KeyMemory with {len(self._anchors)} anchors>"
    
    def keys(self):
        """Get all anchor names"""
        return self._anchors.keys()
    
    def values(self):
        """Get all anchor values"""
        return self._anchors.values()
    
    def items(self):
        """Get all anchor items"""
        return self._anchors.items()
    
    def to_dict(self) -> Dict[str, str]:
        """
        Export as dictionary
        
        Returns:
            Dictionary copy of anchors
        """
        return dict(self._anchors)
