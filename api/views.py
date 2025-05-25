# api/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView # Keep this import for inheritance

# Import the serializers
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
    MyTokenObtainPairSerializer # Import your custom JWT serializer
)
# Import the models
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

# --- Custom Permissions (No changes needed here) ---
class IsStaffUser(BasePermission):
    """Allows access only to staff users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class IsTeacherUser(BasePermission):
    """Allows access only to authenticated users linked to a Professor."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'professor_profile')

class IsStudentUser(BasePermission):
    """Allows access only to authenticated users linked to an Aluno."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'aluno_profile')

class IsGuardianUser(BasePermission):
    """Allows access only to authenticated users linked to a Responsavel."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'responsavel_profile')

class IsStaffOrTeacher(BasePermission):
    """Allows access only to staff or teacher users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_staff or hasattr(request.user, 'professor_profile'))

class IsStudentOrGuardian(BasePermission):
    """Allows access only to student or guardian users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (hasattr(request.user, 'aluno_profile') or hasattr(request.user, 'responsavel_profile'))

class CanViewData(BasePermission):
    """Allows access to Staff, Teachers, Students, or Guardians."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            hasattr(request.user, 'professor_profile') or
            hasattr(request.user, 'aluno_profile') or
            hasattr(request.user, 'responsavel_profile')
        )


# --- Custom JWT View (Moved to top of ViewSets section for explicit definition order) ---
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens, using MyTokenObtainPairSerializer.
    """
    serializer_class = MyTokenObtainPairSerializer


# --- ViewSets with Role-Based Access and Data Filtering ---

class AdministracaoViewSet(viewsets.ModelViewSet):
    """ViewSet for the Administracao model - Full CRUD for Staff."""
    queryset = Administracao.objects.all()
    serializer_class = AdministracaoSerializer
    permission_classes = [IsStaffUser]


class ProfessoresViewSet(viewsets.ModelViewSet):
    """ViewSet for the Professores model - Full CRUD for Staff, Read-only for Teachers (their own record)."""
    queryset = Professores.objects.all()
    serializer_class = ProfessoresSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Professores.objects.all()
        # If the user is a Teacher, they can only view their own profile linked to their user account
        if hasattr(user, 'professor_profile'):
            return Professores.objects.filter(user=user) # Filter by the linked User object directly
        return Professores.objects.none()

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             return [IsAuthenticated(), IsStaffOrTeacher()]
        return [IsStaffUser()]


class ResponsaveisViewSet(viewsets.ModelViewSet):
    """ViewSet for the Responsaveis model - Full CRUD for Staff, Read-only for Guardians (their own record)."""
    queryset = Responsaveis.objects.all()
    serializer_class = ResponsaveisSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Responsaveis.objects.all()
        if hasattr(user, 'responsavel_profile'):
             return Responsaveis.objects.filter(user=user) # Filter by the linked User object directly
        return Responsaveis.objects.none()

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             return [IsAuthenticated(), CanViewData()]
        return [IsStaffUser()]


class AlunosViewSet(viewsets.ModelViewSet):
    """ViewSet for the Alunos model - Full CRUD for Staff, Read-only for Teachers/Students/Guardians."""
    queryset = Alunos.objects.all()
    serializer_class = AlunosSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Alunos.objects.all()
        if hasattr(user, 'professor_profile'):
             teacher_classes = user.professor_profile.classes.all()
             student_ids = set()
             for class_obj in teacher_classes:
                 student_ids.update(class_obj.alunos.values_list('id', flat=True))
             return Alunos.objects.filter(id__in=list(student_ids))
        # If the user is a Student, they can only view their own profile linked to their user account
        if hasattr(user, 'aluno_profile'):
             return Alunos.objects.filter(user=user) # Filter by the linked User object directly
        if hasattr(user, 'responsavel_profile'):
             return user.responsavel_profile.alunos.all()
        return Alunos.objects.none()

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             return [IsAuthenticated(), CanViewData()]
        return [IsStaffUser()]


class MateriasViewSet(viewsets.ModelViewSet):
    """ViewSet for the Materias model - Full CRUD for Staff, Read-only for others."""
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
    """ViewSet for the Classes model - Full CRUD for Staff, Read-only for others."""
    queryset = Classes.objects.all()
    serializer_class = ClassesSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or hasattr(user, 'professor_profile'):
            return Classes.objects.all()
        if hasattr(user, 'aluno_profile'):
            return user.aluno_profile.classes.all()
        if hasattr(user, 'responsavel_profile'):
            student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
            return Classes.objects.filter(alunos__id__in=list(student_ids)).distinct()
        return Classes.objects.none()


    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             return [IsAuthenticated(), CanViewData()]
        return [IsStaffUser()]


class AvaliacoesViewSet(viewsets.ModelViewSet):
    """ViewSet for the Avaliacoes model - CRUD for Staff/Teachers, Read-only for Students/Guardians."""
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
    """ViewSet for the Notas model - CRUD for Staff/Teachers, Read-only for Students/Guardians."""
    queryset = Notas.objects.all()
    serializer_class = NotasSerializer
    permission_classes = [IsAuthenticated, CanViewData]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notas.objects.all()
        if hasattr(user, 'professor_profile'):
             assigned_notes = Notas.objects.filter(atribuida_por=user.professor_profile)
             teacher_classes = user.professor_profile.classes.all()
             student_ids = set()
             for class_obj in teacher_classes:
                 student_ids.update(class_obj.alunos.values_list('id', flat=True))
             notes_for_my_students = Notas.objects.filter(aluno__id__in=list(student_ids))
             return (assigned_notes | notes_for_my_students).distinct()
        if hasattr(user, 'aluno_profile'):
             return Notas.objects.filter(aluno=user.aluno_profile)
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
