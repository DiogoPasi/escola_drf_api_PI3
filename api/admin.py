from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    Administracao,
    Professores,
    Responsaveis,
    Alunos,
    Materias,
    Classes,
    Avaliacoes,
    Notas
)

# Link profile > User em Admin
class AdministracaoInline(admin.StackedInline):
    model = Administracao
    can_delete = False
    verbose_name_plural = 'administracao profile'

class ProfessoresInline(admin.StackedInline):
    model = Professores
    can_delete = False
    verbose_name_plural = 'professor profile'

class AlunosInline(admin.StackedInline):
    model = Alunos
    can_delete = False
    verbose_name_plural = 'aluno profile'

class ResponsaveisInline(admin.StackedInline):
    model = Responsaveis
    can_delete = False
    verbose_name_plural = 'responsavel profile'


# Extend the default User admin
class UserAdmin(BaseUserAdmin):
    inlines = (AdministracaoInline, ProfessoresInline, AlunosInline, ResponsaveisInline)

# Re-register User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Models
admin.site.register(Materias)
admin.site.register(Classes)
admin.site.register(Avaliacoes)
admin.site.register(Notas)
# Ocultar se administrar somente via User admin
admin.site.register(Administracao)
admin.site.register(Professores)
admin.site.register(Responsaveis)
admin.site.register(Alunos)