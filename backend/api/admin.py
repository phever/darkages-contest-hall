from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Contest, Entry, VoteIntention, WorkflowStep


STEP_LABELS = {
    1: 'Submission',
    2: 'Review',
    3: 'Loures Confirmation',
    4: 'Nobility Awarded',
}


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'in_game_name', 'role', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Contest Hall', {'fields': ('role', 'is_verified', 'in_game_name')}),
    )


class EntryInline(admin.TabularInline):
    model = Entry
    extra = 0
    fields = ('entrant_name', 'work_title', 'work_subject', 'current_step', 'recommendation')
    show_change_link = True


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'entry_count')
    inlines = [EntryInline]

    @admin.display(description='Entries')
    def entry_count(self, obj):
        return obj.entries.count()


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    ordering = ('number',)


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = (
        'entrant_name', 'work_title', 'work_subject', 'on_step',
        'recommendation', 'review_overseer', 'contest',
    )
    list_filter = ('work_subject', 'current_step', 'recommendation', 'contest')
    search_fields = ('entrant_name', 'work_title', 'review_overseer')
    actions = ('advance_step', 'mark_nobility_awarded')
    fieldsets = (
        ('Work', {'fields': ('contest', 'entrant_name', 'work_title', 'work_subject', 'content')}),
        ('Locations', {'fields': ('original_location_url', 'original_location_label', 'archived_location_url')}),
        ('Review', {'fields': ('review_overseer', 'review_opened', 'review_closed', 'review_closes_at', 'recommendation')}),
        ('Workflow', {'fields': ('current_step', 'step_status')}),
    )

    @admin.display(description='On Step')
    def on_step(self, obj):
        return obj.on_step

    @admin.action(description='Advance to next step')
    def advance_step(self, request, queryset):
        updated = 0
        for entry in queryset:
            if entry.current_step < Entry.TOTAL_STEPS:
                entry.current_step += 1
                entry.step_status = STEP_LABELS.get(entry.current_step, entry.step_status)
                entry.save(update_fields=['current_step', 'step_status'])
                updated += 1
        self.message_user(request, f"Advanced {updated} entr(y/ies).")

    @admin.action(description='Mark as Nobility Awarded (4/4)')
    def mark_nobility_awarded(self, request, queryset):
        updated = queryset.update(current_step=4, step_status='Nobility Awarded')
        self.message_user(request, f"Marked {updated} entr(y/ies) as Nobility Awarded.")


@admin.register(VoteIntention)
class VoteIntentionAdmin(admin.ModelAdmin):
    list_display = ('user', 'entry', 'recommendation', 'remind_before_close', 'updated_at')
    list_filter = ('recommendation', 'remind_before_close')
    search_fields = ('user__username', 'entry__work_title')
