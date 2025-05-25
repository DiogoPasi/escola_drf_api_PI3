# api/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q # Import Q object for complex lookups
from django.contrib.auth.models import User # Import User model
from rest_framework.generics import CreateAPIView # Import CreateAPIView for registration
from rest_framework_simplejwt.views import TokenObtainPairView # Import for custom view

# Import the serializers we just created
from .serializers import (
    AdministracaoSerializer,
    ProfessoresSerializer,
    ResponsaveisSerializer,
    AlunosSerializer,
    MateriasSerializer,
    ClassesSerializer,
    AvaliacoesSerializer,
    NotasSerializer,
    RegistroUsuarioSerializer, # Import the new serializer
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

# --- Custom Permissions ---
# These check if the authenticated user is linked to the respective model instance

class IsStaffUser(BasePermission):
    """Allows access only to staff users."""
    def has_permission(self, request, view):
        # User must be authenticated and have the is_staff flag set
        return request.user and request.user.is_authenticated and request.user.is_staff

class IsTeacherUser(BasePermission):
    """Allows access only to authenticated users linked to a Professor."""
    def has_permission(self, request, view):
        # User must be authenticated and have a linked professor_profile
        return request.user and request.user.is_authenticated and hasattr(request.user, 'professor_profile')

class IsStudentUser(BasePermission):
    """Allows access only to authenticated users linked to an Aluno."""
    def has_permission(self, request, view):
        # User must be authenticated and have a linked aluno_profile
        return request.user and request.user.is_authenticated and hasattr(request.user, 'aluno_profile')

class IsGuardianUser(BasePermission):
    """Allows access only to authenticated users linked to a Responsavel."""
    def has_permission(self, request, view):
        # User must be authenticated and have a linked responsavel_profile
        return request.user and request.user.is_authenticated and hasattr(request.user, 'responsavel_profile')

class IsStaffOrTeacher(BasePermission):
    """Allows access only to staff or teacher users."""
    def has_permission(self, request, view):
        # User must be authenticated and be either staff or have a professor profile
        return request.user and request.user.is_authenticated and (request.user.is_staff or hasattr(request.user, 'professor_profile'))

class IsStudentOrGuardian(BasePermission):
    """Allows access only to student or guardian users."""
    def has_permission(self, request, view):
        # User must be authenticated and be either a student or a guardian
        return request.user and request.user.is_authenticated and (hasattr(request.user, 'aluno_profile') or hasattr(request.user, 'responsavel_profile'))

class CanViewData(BasePermission):
    """Allows access to Staff, Teachers, Students, or Guardians."""
    def has_permission(self, request, view):
        # User must be authenticated and belong to one of the allowed roles
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            hasattr(request.user, 'professor_profile') or
            hasattr(request.user, 'aluno_profile') or
            hasattr(request.user, 'responsavel_profile')
        )


# --- ViewSets with Role-Based Access and Data Filtering ---

class AdministracaoViewSet(viewsets.ModelViewSet):
    """ViewSet for the Administracao model - Full CRUD for Staff."""
    queryset = Administracao.objects.all()
    serializer_class = AdministracaoSerializer
    # Only Staff can perform CRUD on Staff records
    permission_classes = [IsStaffUser]


class ProfessoresViewSet(viewsets.ModelViewSet):
    """ViewSet for the Professores model - Full CRUD for Staff, Read-only for Teachers (their own record)."""
    queryset = Professores.objects.all()
    serializer_class = ProfessoresSerializer
    # Staff can CRUD, Teachers can only view their own record, others cannot access
    permission_classes = [IsAuthenticated, CanViewData] # Requires auth, must be Staff OR Teacher OR Student/Guardian to access at all

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Professores.objects.all()
        # If the user is a Teacher, they can only view their own profile
        if hasattr(user, 'professor_profile'): # Check the linked profile name
            return Professores.objects.filter(pk=user.professor_profile.pk)
        # Should not reach here due to permissions, but return empty for safety
        return Professores.objects.none()

    def get_permissions(self):
        # Allow only safe methods (GET, HEAD, OPTIONS) for viewing
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             # Staff can view all, Teachers can view their own
             return [IsAuthenticated(), IsStaffOrTeacher()]
        # For unsafe methods (POST, PUT, PATCH, DELETE), only Staff are allowed
        return [IsStaffUser()]


class ResponsaveisViewSet(viewsets.ModelViewSet):
    """ViewSet for the Responsaveis model - Full CRUD for Staff, Read-only for Guardians (their own record)."""
    queryset = Responsaveis.objects.all()
    serializer_class = ResponsaveisSerializer
    # Staff can CRUD, Guardians can only view their own record, others cannot access
    # Use CanViewData for read access, IsStaffUser for write access
    permission_classes = [IsAuthenticated, CanViewData] # Requires auth, must be Staff OR Teacher OR Student/Guardian to access at all

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Responsaveis.objects.all()
        if hasattr(user, 'responsavel_profile'): # Check the linked profile name
             return Responsaveis.objects.filter(pk=user.responsavel_profile.pk)

        # Should not reach here due to permissions, but return empty for safety
        return Responsaveis.objects.none()

    def get_permissions(self):
        # Allow only safe methods (GET, HEAD, OPTIONS) for viewing
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             # Staff or Guardians can view their relevant data
             return [IsAuthenticated(), CanViewData()] # Use the new combined permission class instance
        # For unsafe methods (POST, PUT, PATCH, DELETE), only Staff are allowed
        return [IsStaffUser()]


class AlunosViewSet(viewsets.ModelViewSet):
    """ViewSet for the Alunos model - Full CRUD for Staff, Read-only for Teachers/Students/Guardians."""
    queryset = Alunos.objects.all()
    serializer_class = AlunosSerializer
    # Staff can CRUD, Teachers/Students/Guardians can view their relevant students
    permission_classes = [IsAuthenticated, CanViewData] # Requires auth, must be Staff OR Teacher OR Student/Guardian to access at all

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Alunos.objects.all()
        # If the user is a Teacher, return students in their classes
        if hasattr(user, 'professor_profile'): # Check the linked profile name
             teacher_classes = user.professor_profile.classes.all()
             student_ids = set()
             for class_obj in teacher_classes:
                 student_ids.update(class_obj.alunos.values_list('id', flat=True))
             return Alunos.objects.filter(id__in=list(student_ids))
        # If the user is a Student, they can only view their own profile
        if hasattr(user, 'aluno_profile'): # Check the linked profile name
             return Alunos.objects.filter(pk=user.aluno_profile.pk)
        # If the user is a Guardian, return their linked students
        if hasattr(user, 'responsavel_profile'): # Check the linked profile name
             return user.responsavel_profile.alunos.all()

        # Should not reach here due to permissions, but return empty for safety
        return Alunos.objects.none()

    def get_permissions(self):
        # Allow only safe methods (GET, HEAD, OPTIONS) for viewing
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             # Staff, Teachers, Students, Guardians can view
             return [IsAuthenticated(), CanViewData()] # Use the new combined permission class instance
        # For unsafe methods (POST, PUT, PATCH, DELETE), only Staff are allowed
        return [IsStaffUser()]


class MateriasViewSet(viewsets.ModelViewSet):
    """ViewSet for the Materias model - Full CRUD for Staff, Read-only for others."""
    queryset = Materias.objects.all()
    serializer_class = MateriasSerializer
    # Staff can CRUD, others can view their relevant subjects
    permission_classes = [IsAuthenticated, CanViewData] # Requires auth, must be Staff OR Teacher OR Student/Guardian to access at all

    def get_queryset(self):
        user = self.request.user
        # If the user is Staff (Admin) or Teacher, return all subjects
        if user.is_staff or hasattr(user, 'professor_profile'): # Check the linked profile name
            return Materias.objects.all()
        # If the user is a Student, return subjects for their classes
        if hasattr(user, 'aluno_profile'): # Check the linked profile name
            student_classes = user.aluno_profile.classes.all()
            subject_ids = set()
            for class_obj in student_classes:
                subject_ids.update(class_obj.materias.values_list('id', flat=True))
            return Materias.objects.filter(id__in=list(subject_ids))
        # If the user is a Guardian, return subjects for their linked students' classes
        if hasattr(user, 'responsavel_profile'): # Check the linked profile name
            student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
            # Find all classes for these students
            student_classes = Classes.objects.filter(alunos__id__in=list(student_ids))
            subject_ids = set()
            for class_obj in student_classes:
                 subject_ids.update(class_obj.materias.values_list('id', flat=True))
            return Materias.objects.filter(id__in=list(subject_ids))

        # Should not reach here due to permissions, but return empty for safety
        return Materias.objects.none()

    def get_permissions(self):
        # Allow only safe methods (GET, HEAD, OPTIONS) for viewing
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             # Staff, Teachers, Students, Guardians can view
             return [IsAuthenticated(), CanViewData()] # Use the new combined permission class instance
        # For unsafe methods (POST, PUT, PATCH, DELETE), only Staff are allowed
        return [IsStaffUser()]


class ClassesViewSet(viewsets.ModelViewSet):
    """ViewSet for the Classes model - Full CRUD for Staff, Read-only for others."""
    queryset = Classes.objects.all()
    serializer_class = ClassesSerializer
    # Staff can CRUD, others can view their relevant classes
    permission_classes = [IsAuthenticated, CanViewData] # Requires auth, must be Staff OR Teacher OR Student/Guardian to access at all

    def get_queryset(self):
        user = self.request.user
        # If the user is Staff (Admin) or Teacher, return all classes (Teachers might need to see all or just their own)
        # Let's assume Teachers see all classes for now as per previous logic
        if user.is_staff or hasattr(user, 'professor_profile'): # Check the linked profile name
            return Classes.objects.all()
        # If the user is a Student, return their classes
        if hasattr(user, 'aluno_profile'): # Check the linked profile name
            return user.aluno_profile.classes.all()
        # If the user is a Guardian, return classes for their linked students
        if hasattr(user, 'responsavel_profile'): # Check the linked profile name
            student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
            return Classes.objects.filter(alunos__id__in=list(student_ids)).distinct() # Use distinct to avoid duplicates

        # Should not reach here due to permissions, but return empty for safety
        return Classes.objects.none()


    def get_permissions(self):
        # Allow only safe methods (GET, HEAD, OPTIONS) for viewing
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             # Staff, Teachers, Students, Guardians can view
             return [IsAuthenticated(), CanViewData()] # Use the new combined permission class instance
        # For unsafe methods (POST, PUT, PATCH, DELETE), only Staff are allowed
        return [IsStaffUser()]


class AvaliacoesViewSet(viewsets.ModelViewSet):
    """ViewSet for the Avaliacoes model - CRUD for Staff/Teachers, Read-only for Students/Guardians."""
    queryset = Avaliacoes.objects.all()
    serializer_class = AvaliacoesSerializer
    # Staff/Teachers can CRUD, Students/Guardians can view their relevant assessments
    permission_classes = [IsAuthenticated, CanViewData] # Requires auth, must be Staff OR Teacher OR Student/Guardian to access at all

    def get_queryset(self):
        user = self.request.user
        # If the user is Staff (Admin) or Teacher, return all assessments
        if user.is_staff or hasattr(user, 'professor_profile'): # Check the linked profile name
            return Avaliacoes.objects.all()
        # If the user is a Student or Guardian, return assessments linked to their/their linked students' subjects/classes
        if hasattr(user, 'aluno_profile'): # Check the linked profile name for Student
            student_classes = user.aluno_profile.classes.all()
            subject_ids = set()
            for class_obj in student_classes:
                subject_ids.update(class_obj.materias.values_list('id', flat=True))
            # Return assessments linked to these subjects or the responsible teacher's classes
            return Avaliacoes.objects.filter(Q(responsavel_por__classes__in=student_classes) | Q(materias__id__in=list(subject_ids))).distinct()

        if hasattr(user, 'responsavel_profile'): # Check the linked profile name for Guardian
            student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
            student_classes = Classes.objects.filter(alunos__id__in=list(student_ids))
            subject_ids = set()
            for class_obj in student_classes:
                 subject_ids.update(class_obj.materias.values_list('id', flat=True))
            # Return assessments linked to these subjects or the responsible teacher's classes
            return Avaliacoes.objects.filter(Q(responsavel_por__classes__in=student_classes) | Q(materias__id__in=list(subject_ids))).distinct()


        # Should not reach here due to permissions, but return empty for safety
        return Avaliacoes.objects.none()

    def get_permissions(self):
        # Allow only safe methods (GET, HEAD, OPTIONS) for viewing
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             # Staff, Teachers, Students, Guardians can view
             return [IsAuthenticated(), CanViewData()] # Use the new combined permission class instance
        # For unsafe methods (POST, PUT, PATCH, DELETE), only Staff or Teachers are allowed
        return [IsStaffOrTeacher()]


class NotasViewSet(viewsets.ModelViewSet):
    """ViewSet for the Notas model - CRUD for Staff/Teachers, Read-only for Students/Guardians."""
    queryset = Notas.objects.all()
    serializer_class = NotasSerializer
    # Staff/Teachers can CRUD, Students/Guardians can view their own/linked students' notes
    permission_classes = [IsAuthenticated, CanViewData] # Requires auth, must be Staff OR Teacher OR Student/Guardian to access at all

    def get_queryset(self):
        user = self.request.user
        # If the user is Staff (Admin), return all notes
        if user.is_staff:
            return Notas.objects.all()
        # If the user is a Teacher, return notes they assigned or notes for students in their classes
        if hasattr(user, 'professor_profile'): # Check the linked profile name
             # Option 1: Notes assigned by this teacher
             assigned_notes = Notas.objects.filter(atribuida_por=user.professor_profile)
             # Option 2: Notes for students in this teacher's classes
             teacher_classes = user.professor_profile.classes.all()
             student_ids = set()
             for class_obj in teacher_classes:
                 student_ids.update(class_obj.alunos.values_list('id', flat=True))
             notes_for_my_students = Notas.objects.filter(aluno__id__in=list(student_ids))
             # Combine and return unique notes
             return (assigned_notes | notes_for_my_students).distinct()
        # If the user is a Student, return their own notes
        if hasattr(user, 'aluno_profile'): # Check the linked profile name
             return Notas.objects.filter(aluno=user.aluno_profile)
        # If the user is a Guardian, return notes for their linked students
        if hasattr(user, 'responsavel_profile'): # Check the linked profile name
             student_ids = user.responsavel_profile.alunos.values_list('id', flat=True)
             return Notas.objects.filter(aluno__id__in=list(student_ids))

        # Should not reach here due to permissions, but return empty for safety
        return Notas.objects.none()

    def get_permissions(self):
        # Allow only safe methods (GET, HEAD, OPTIONS) for viewing
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
             # Staff, Teachers, Students, Guardians can view
             return [IsAuthenticated(), CanViewData()] # Use the new combined permission class instance
        # For unsafe methods (POST, PUT, PATCH, DELETE), only Staff or Teachers are allowed
        return [IsStaffOrTeacher()]

# Registro de Usuários

class RegistroUsuarioView(CreateAPIView):
    """
    Endpoint para cadastro de novos usuários.
    """
    queryset = User.objects.all()
    serializer_class = RegistroUsuarioSerializer
    permission_classes = [AllowAny]

# Custom JWT View (Keep this as it is)
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

