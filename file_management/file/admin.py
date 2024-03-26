from django.contrib import admin

from file.models import DeleteAccess, File, ReadAccess, WriteAccess

class ReadAccessInline(admin.TabularInline):
    model = ReadAccess

class WriteAccessInline(admin.TabularInline):
    model = WriteAccess

class DeleteAccessInline(admin.TabularInline):
    model = DeleteAccess

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'file', 'updated_at', 'file_owner')
    inlines = [ReadAccessInline, WriteAccessInline, DeleteAccessInline]