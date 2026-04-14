"""
Demonstrates nested models and generic patterns in Pydantic v2.

Key concepts covered:
- Nested model composition with forward references
- Recursive models (tree structures)
- Generic models for reusable response wrappers
- Self-referencing models with model_rebuild()
- Optional nested models with default factories
- Nested validation error propagation

Real-world use cases:
- Organizational hierarchies (departments, teams)
- Comment threads (nested replies)
- API response standardization (PaginatedResponse[T])
- Configuration trees with inheritance
"""

from pydantic import BaseModel, Field, computed_field, model_validator
from typing import Optional, List, Dict, Any, Generic, TypeVar, Self, Union
from datetime import datetime
from enum import StrEnum


# === Forward reference example: Nested Address ===

class Address(BaseModel):
    """
    Reusable address model for nested composition.
    
    Used in User, Order, Company, etc.
    """
    street: str = Field(min_length=5, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: str = Field(min_length=2, max_length=2)  # ISO alpha-2
    postal_code: Optional[str] = Field(default=None, max_length=20)
    
    @computed_field
    @property
    def formatted(self) -> str:
        """Return human-readable address format."""
        parts = [self.street, self.city]
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(p for p in parts if p)


# === Nested model: User with Address ===

class UserProfile(BaseModel):
    """User profile with nested address and preferences."""
    
    id: int
    username: str
    email: str
    
    # Nested model (required)
    address: Address
    
    # Optional nested model
    billing_address: Optional[Address] = None
    
    # Nested dict with structure
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # List of nested models
    emergency_contacts: List["Contact"] = Field(default_factory=list)
    
    @computed_field
    @property
    def has_billing_address(self) -> bool:
        """Convenience property for API responses."""
        return self.billing_address is not None


# === Forward reference for Contact (defined after UserProfile) ===

class Contact(BaseModel):
    """Emergency contact with nested address."""
    name: str
    relationship: str
    phone: str
    address: Optional[Address] = None


# Rebuild models with forward references
UserProfile.model_rebuild()


# === Recursive model: Comment Thread ===

class Comment(BaseModel):
    """
    Recursive comment model for nested replies.
    
    Each comment can have child comments (replies).
    """
    id: int
    author: str
    content: str = Field(min_length=1, max_length=5000)
    created_at: datetime
    
    # Self-referencing: list of child comments
    replies: List["Comment"] = Field(default_factory=list)
    
    # Computed: total reply count (recursive)
    @computed_field
    @property
    def total_replies(self) -> int:
        """Count all nested replies recursively."""
        return len(self.replies) + sum(r.total_replies for r in self.replies)
    
    # Computed: flat list of all reply IDs
    @computed_field
    @property
    def all_reply_ids(self) -> List[int]:
        """Get IDs of all nested replies (depth-first)."""
        ids = [r.id for r in self.replies]
        for r in self.replies:
            ids.extend(r.all_reply_ids)
        return ids


# Rebuild for recursive reference
Comment.model_rebuild()


# === Generic response wrapper ===

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response for list endpoints.
    
    Usage:
        PaginatedResponse[User](items=[...], total=100, page=1, per_page=20)
        PaginatedResponse[Comment](...)
    
    Benefits:
    - Type-safe item access
    - Consistent API response structure
    - Reusable across all list endpoints
    """
    
    items: List[T] = Field(description="List of items for current page")
    total: int = Field(ge=0, description="Total items across all pages")
    
    page: int = Field(ge=1, default=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, default=20, description="Items per page")
    
    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total pages (ceiling division)."""
        if self.per_page == 0:
            return 0
        return -(-self.total // self.per_page)
    
    @computed_field
    @property
    def has_next(self) -> bool:
        """Check if next page exists."""
        return self.page < self.total_pages
    
    @computed_field
    @property
    def has_previous(self) -> bool:
        """Check if previous page exists."""
        return self.page > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return self.model_dump(mode="json", exclude_none=True)


# === Nested generics: Tree structure ===

class TreeNode(BaseModel, Generic[T]):
    """
    Generic tree node for hierarchical data.
    
    Usage:
        TreeNode[Department](value=dept, children=[...])
        TreeNode[Category](...)
    """
    
    value: T
    children: List["TreeNode[T]"] = Field(default_factory=list)
    
    @computed_field
    @property
    def depth(self) -> int:
        """Calculate max depth of this subtree."""
        if not self.children:
            return 1
        return 1 + max(child.depth for child in self.children)
    
    @computed_field
    @property
    def node_count(self) -> int:
        """Count total nodes in subtree."""
        return 1 + sum(child.node_count for child in self.children)
    
    def flatten(self) -> List[T]:
        """Flatten tree to list (depth-first traversal)."""
        result = [self.value]
        for child in self.children:
            result.extend(child.flatten())
        return result


TreeNode.model_rebuild()


# === Real-world example: Organization hierarchy ===

class Department(BaseModel):
    """Department with nested sub-departments and employees."""
    
    id: int
    name: str
    code: str = Field(pattern=r"^[A-Z]{2,5}$")  # e.g., "ENG", "MKT"
    
    # Self-referencing nested departments
    sub_departments: List["Department"] = Field(default_factory=list)
    
    # Nested employee list
    employees: List["Employee"] = Field(default_factory=list)
    
    manager: Optional["Employee"] = None
    
    @computed_field
    @property
    def total_employees(self) -> int:
        """Count employees in this dept and all sub-depts."""
        direct = len(self.employees)
        sub_total = sum(sd.total_employees for sd in self.sub_departments)
        return direct + sub_total
    
    @computed_field
    @property
    def full_path(self) -> str:
        """Get department path like "Company > Engineering > Backend"."""
        # Would need parent reference in real implementation
        return self.name


class Employee(BaseModel):
    """Employee with nested department reference."""
    
    id: int
    name: str
    email: str
    department: Optional[Department] = None
    
    # Nested address
    work_location: Optional[Address] = None


# Rebuild for circular references
Department.model_rebuild()
Employee.model_rebuild()


# === Discriminated union in nested context ===

class NotificationSettings(BaseModel):
    """Base notification settings."""
    enabled: bool = True


class EmailSettings(NotificationSettings):
    """Email-specific notification settings."""
    channel: str = "email"
    address: str
    frequency: str = Field(pattern="^(immediate|daily|weekly)$")


class SMSSettings(NotificationSettings):
    """SMS-specific notification settings."""
    channel: str = "sms"
    phone: str
    timezone: str = Field(default="UTC", pattern=r"^[A-Z]{3,5}$")


class PushSettings(NotificationSettings):
    """Push notification settings."""
    channel: str = "push"
    device_tokens: List[str] = Field(default_factory=list, max_length=5)


# Union of notification types
NotificationConfig = Union[EmailSettings, SMSSettings, PushSettings]


class UserNotificationPreferences(BaseModel):
    """User preferences with discriminated union for notifications."""
    
    user_id: int
    global_enabled: bool = True
    
    # List of different notification configs
    channels: List[NotificationConfig] = Field(default_factory=list)
    
    @model_validator(mode="after")
    def validate_channel_uniqueness(self) -> Self:
        """Ensure no duplicate channel types."""
        channels = [c.channel for c in self.channels]
        if len(channels) != len(set(channels)):
            raise ValueError("Each notification channel can only be configured once")
        return self