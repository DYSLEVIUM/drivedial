from django.db import models


class CallSummaryShort(models.Model):
    """Stores a concise 3-line summary of each call."""

    call_id = models.CharField(max_length=50, unique=True, db_index=True)
    phone_number = models.CharField(max_length=20, db_index=True)
    summary = models.TextField(
        help_text="Exactly 3 lines summarizing this call")
    keywords = models.JSONField(
        default=list, help_text="Max 5 important keywords/phrases from this call")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', '-created_at']),
        ]

    def __str__(self):
        return f"Call {self.call_id} - {self.phone_number}"


class CustomerProfile(models.Model):
    """Stores rolling summary and keywords for each customer across all calls."""

    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    rolling_summary = models.TextField(
        help_text="Exactly 3 lines - rolling summary of all interactions")
    keywords = models.JSONField(
        default=list, help_text="Cumulative list of important keywords/phrases (max 50)")
    total_calls = models.IntegerField(default=0)
    last_call_id = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Profile: {self.phone_number} ({self.total_calls} calls)"

    def add_keywords(self, new_keywords: list, max_total: int = 50):
        """Add new keywords, keeping only the most recent ones up to max_total."""
        self.keywords.extend(new_keywords)
        if len(self.keywords) > max_total:
            self.keywords = self.keywords[-max_total:]

    def to_context_string(self) -> str:
        """Generate context string for AI prompt."""
        context_parts = [
            f"**CUSTOMER PROFILE**: {self.customer_name or 'Name unknown'}",
            f"**RELATIONSHIP SUMMARY** (from all {self.total_calls} previous calls):",
            self.rolling_summary,
        ]

        if self.keywords:
            keywords_str = ", ".join(self.keywords[-10:])
            context_parts.append(f"\n**IMPORTANT CONTEXT**: {keywords_str}")

        return "\n".join(context_parts)


class CallSummary(models.Model):
    """Stores call summary and analysis for each customer interaction."""

    # Identifiers
    call_id = models.CharField(max_length=50, unique=True, db_index=True)
    phone_number = models.CharField(max_length=20, db_index=True)

    # Customer info (extracted from conversation)
    customer_name = models.CharField(max_length=100, blank=True, null=True)

    # Call summary
    summary = models.TextField(help_text="2-3 line summary of the call")

    # Keywords/Tags (stored as JSON)
    lead_quality = models.CharField(
        max_length=20,
        choices=[
            ('HOT', 'Hot'),
            ('WARM', 'Warm'),
            ('COLD', 'Cold'),
        ],
        default='WARM'
    )
    purchase_likelihood = models.CharField(
        max_length=20,
        choices=[
            ('HIGH', 'High'),
            ('MEDIUM', 'Medium'),
            ('LOW', 'Low'),
        ],
        default='MEDIUM'
    )
    call_outcome = models.CharField(
        max_length=30,
        choices=[
            ('BOOKING_CONFIRMED', 'Booking Confirmed'),
            ('INTERESTED', 'Interested'),
            ('CALLBACK_REQUESTED', 'Callback Requested'),
            ('TRANSFERRED', 'Transferred to Agent'),
            ('DROPPED', 'Dropped'),
            ('NOT_INTERESTED', 'Not Interested'),
        ],
        default='DROPPED'
    )

    # Product preferences (extracted)
    items_discussed = models.JSONField(
        default=list, help_text="List of items/products discussed")
    preferred_item = models.CharField(
        max_length=100, blank=True, null=True, help_text="The main item/product customer showed interest in")
    preferred_color = models.CharField(max_length=50, blank=True, null=True)
    budget_range = models.CharField(max_length=50, blank=True, null=True)

    # Key concerns/objections
    objections = models.JSONField(
        default=list, help_text="List of objections raised")

    # Metadata
    call_duration_seconds = models.IntegerField(default=0)
    is_latest = models.BooleanField(default=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', '-created_at']),
            models.Index(fields=['phone_number', 'is_latest']),
        ]

    def __str__(self):
        return f"Call {self.call_id} - {self.phone_number} ({self.call_outcome})"

    def save(self, *args, **kwargs):
        # Mark previous calls from same phone number as not latest
        if self.is_latest:
            CallSummary.objects.filter(
                phone_number=self.phone_number,
                is_latest=True
            ).exclude(pk=self.pk).update(is_latest=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_latest_for_phone(cls, phone_number: str):
        """Get the most recent call summary for a phone number."""
        return cls.objects.filter(
            phone_number=phone_number,
            is_latest=True
        ).first()

    @classmethod
    def get_history_for_phone(cls, phone_number: str, limit: int = 5):
        """Get call history for a phone number."""
        return list(cls.objects.filter(
            phone_number=phone_number
        ).order_by('-created_at')[:limit])

    def to_context_string(self) -> str:
        """Generate a context string for the AI prompt."""
        context_parts = [
            f"**RETURNING CUSTOMER**: {self.customer_name or 'Name unknown'}",
            f"**Last Call Summary**: {self.summary}",
            f"**Lead Quality**: {self.lead_quality}",
            f"**Previous Interest**: {self.preferred_item or 'Not specified'}",
        ]

        if self.preferred_color:
            context_parts.append(
                f"**Preferred Color**: {self.preferred_color}")

        if self.budget_range:
            context_parts.append(f"**Budget**: {self.budget_range}")

        if self.objections:
            context_parts.append(
                f"**Previous Objections**: {', '.join(self.objections)}")

        if self.items_discussed:
            context_parts.append(
                f"**Items Discussed Before**: {', '.join(str(item) for item in self.items_discussed[:3])}")

        return "\n".join(context_parts)
