from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, BasePermission
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.auth.models import User
# Serializers 
from .serializers import (
    AdministracaoSerializer,
    ProfessoresSerializer,
    ResponsaveisSerializer,
    AlunosSerializer,
    MateriasSerializer,
    ClassesSerializer,
    AvaliacoesSerializer,
    NotasSerializer,
    RegistroUsuarioSerializer,
)
# Models
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

# --- Custom Permissions ---
class IsStaffUser(BasePermission):
    """Acesso para usuários staff."""
    def has_permission(self, request, view):
        # is_staff flag
        return request.user and request.user.is_authenticated and request.user.is_staff

class IsTeacherUser(BasePermission):
    def has_permission(self, request, view):
        # Link com professor_profile
        return request.user and request.user.is_authenticated and hasattr(request.user, 'professor_profile')

class IsStudentUser(BasePermission):
    def has_permission(self, request, view):
        # Link aluno_profile
        return request.user and request.user.is_authenticated and hasattr(request.user, 'aluno_profile')

class IsGuardianUser(BasePermission):
    def has_permission(self, request, view):
        # Link responsavel_profile
        return request.user and request.user.is_authenticated and hasattr(request.user, 'responsavel_profile')

class IsStaffOrTeacher(BasePermission):
    def has_permission(self, request, view):
        return IsStaffUser().has_permission(request, view) or IsTeacherUser().has_permission(request, view)

class IsStudentOrGuardian(BasePermission):
    def has_permission(self, request, view):
        return IsStudentUser().has_permission(request, view) or IsGuardianUser().has_permission(request, view)
    
class CanViewData(BasePermission):
    def has_permission(self, request, view):
        # Usuário deve estar autenticado
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            hasattr(request.user, 'professor_profile') or
            hasattr(request.user, 'aluno_profile') or
            hasattr(request.user, 'responsavel_profile')
        )


# --- ViewSets ---

class AdministracaoViewSet(viewsets.ModelViewSet):
    """ViewSet Administracao - Full CRUD Para Administração."""
    queryset = Administracao.objects.all()
    serializer_class = AdministracaoSerializer
    permission_classes = [IsStaffUser]


class ProfessoresViewSet(viewsets.ModelViewSet):
    """ViewSet Professores - Full CRUD Para Administração."""
    queryset = Professores.objects.all()
    serializer_class = ProfessoresSerializer
    permission_classes = [IsStaffUser]


class ResponsaveisViewSet(viewsets.ModelViewSet):
    """ViewSet Responsaveis - Full CRUD Para Administração, Read-only Responsávies."""
    queryset = Responsaveis.objects.all()
    serializer_class = ResponsaveisSerializer
    # Admin CRUD, Responsável View próprias informações
    permission_classes = [IsAuthenticated, CanViewData] # authentication

    def get_queryset(self):
        user = self.request.user
        # Se usuário(Admin)
        if user.is_staff: # check Para Administração
            return Responsaveis.objects.all()
        # Se usuário (Responsável)
        if hasattr(user, 'responsavel_profile'): # check se usuário tem link com Responsável
             return Responsaveis.objects.filter(pk=user.responsavel.pk)

        # Estudantes e professores
        return Responsaveis.objects.none() # Return empty queryset

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [IsAuthenticated(), CanViewData()]
        return [IsStaffUser()]


class AlunosViewSet(viewsets.ModelViewSet):
    """ViewSet Alunos - Full CRUD Para Administração, Read-only para Outros."""
    queryset = Alunos.objects.all()
    serializer_class = AlunosSerializer
    # Admin CRUD | Outros View dados relacionados
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        # (Admin)
        if user.is_staff:
            return Alunos.objects.all()
        # Professor, return Estudantes na Classe
        if hasattr(user, 'professor'):
             teacher_classes = user.professor_profile.classes.all()
             student_ids = set()
             for class_obj in teacher_classes:
                 student_ids.update(class_obj.alunos.values_list('id', flat=True))
             return Alunos.objects.filter(id__in=list(student_ids))
        # Aluno, return dados relacionados ao usuário
        if hasattr(user, 'aluno_profile'): 
             return Alunos.objects.filter(pk=user.aluno_profile.pk)
        # Responsável, return link Alunos
        if hasattr(user, 'responsavel_profile'): 
             return user.responsavel.alunos.all()

        return Alunos.objects.none()

    def get_permissions(self):
        # (GET, HEAD, OPTIONS) para não Admins
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             return [IsAuthenticated(), CanViewData()]
        return [IsStaffUser()]


class MateriasViewSet(viewsets.ModelViewSet):
    """ViewSet Materias"""
    queryset = Materias.objects.all()
    serializer_class = MateriasSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or hasattr(user, 'professor_profile'):
            return Materias.objects.all()
        if hasattr(user, 'aluno_profile'):
            student_classes = user.aluno_profile.classes.all()
            subject_ids = set()
            for class_obj in student_classes:
                subject_ids.update(class_obj.materias.values_list('id', flat=True))
            return Materias.objects.filter(id__in=list(subject_ids))
        if hasattr(user, 'responsavel_profile'):
            student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
            student_classes = Classes.objects.filter(alunos__id__in=list(student_ids))
            subject_ids = set()
            for class_obj in student_classes:
                 subject_ids.update(class_obj.materias.values_list('id', flat=True))
            return Materias.objects.filter(id__in=list(subject_ids))

        return Materias.objects.none()

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             return [IsAuthenticated(), CanViewData()]
        return [IsStaffUser()]


class ClassesViewSet(viewsets.ModelViewSet):
    queryset = Classes.objects.all()
    serializer_class = ClassesSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or hasattr(user, 'professor_profile'):
            return Classes.objects.all()
        if hasattr(user, 'aluno_profile'):
            return user.aluno_profil.classes.all()
        if hasattr(user, 'responsavel_profile'):
            student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
            return Classes.objects.filter(alunos__id__in=list(student_ids)).distinct()

        return Classes.objects.none()


    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [IsAuthenticated(), CanViewData()]
        return [IsStaffUser()]


class AvaliacoesViewSet(viewsets.ModelViewSet):
    queryset = Avaliacoes.objects.all()
    serializer_class = AvaliacoesSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or hasattr(user, 'professor_profile'):
            return Avaliacoes.objects.all()
        if hasattr(user, 'aluno_profile'):
            student_classes = user.aluno_profile.classes.all()
            subject_ids = set()
            for class_obj in student_classes:
                subject_ids.update(class_obj.materias.values_list('id', flat=True))
            return Avaliacoes.objects.filter(Q(responsavel_por__classes__in=student_classes) | Q(materias__id__in=list(subject_ids))).distinct()

        if hasattr(user, 'responsavel_profile'):
            student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
            student_classes = Classes.objects.filter(alunos__id__in=list(student_ids))
            subject_ids = set()
            for class_obj in student_classes:
                 subject_ids.update(class_obj.materias.values_list('id', flat=True))
            return Avaliacoes.objects.filter(Q(responsavel_por__classes__in=student_classes) | Q(materias__id__in=list(subject_ids))).distinct()

        return Avaliacoes.objects.none()

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [IsAuthenticated(), CanViewData()]
        return [IsStaffOrTeacher()]


class NotasViewSet(viewsets.ModelViewSet):
    queryset = Notas.objects.all()
    serializer_class = NotasSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notas.objects.all()
        if hasattr(user, 'professor_profile'):
             # Option 1: Notas por Professor
             assigned_notes = Notas.objects.filter(atribuida_por=user.professor_profile)
             # Option 2: Notas por Aluno na Classe desse Professor
             teacher_classes = user.professor_profile.classes.all()
             student_ids = set()
             for class_obj in teacher_classes:
                 student_ids.update(class_obj.alunos.values_list('id', flat=True))
             notes_for_my_students = Notas.objects.filter(aluno__id__in=list(student_ids))
             # Combinando
             return (assigned_notes | notes_for_my_students).distinct()
        # Aluno, return Notas
        if hasattr(user, 'aluno_profile'):
             return Notas.objects.filter(aluno=user.aluno_profile)
        # Responsável, return link Alunos
        if hasattr(user, 'responsavel_profile'):
             student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
             return Notas.objects.filter(aluno__id__in=list(student_ids))

        return Notas.objects.none()

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [IsAuthenticated(), CanViewData()]
        return [IsStaffOrTeacher()]


# Registro de Usuários

class RegistroUsuarioView(CreateAPIView):
    """
    Endpoint para cadastro de novos usuários.
    """
    queryset = User.objects.all()
    serializer_class = RegistroUsuarioSerializer
    permission_classes = [AllowAny]