from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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

class AdministracaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administracao
        fields = '__all__' # Todos os campos
        # alternativa: fields = ['id', 'nome', 'cpf', 'email', 'celular']

class ProfessoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professores
        fields = '__all__'
        # fields = ['id', 'nome', 'cpf', 'email', 'celular']

class ResponsaveisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Responsaveis
        fields = '__all__'
        # fields = ['id', 'nome', 'cpf', 'email', 'celular']

class AlunosSerializer(serializers.ModelSerializer):
    # Para ManyToManyField como 'responsaveis', '__all__' serão mostrados os IDs. Ler: SlugRelatedField para melhor customização.
    responsaveis = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Alunos
        fields = '__all__'
        # fields = ['id', 'nome', 'rg', 'data_de_nascimento', 'email', 'celular', 'ra', 'responsaveis']

class MateriasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materias
        fields = '__all__'
        # fields = ['id', 'nome', 'descricao']

class ClassesSerializer(serializers.ModelSerializer):
    # O mesmo para ManyToManyFields como 'alunos', 'professores', 'materias' - '__all__' mostra IDs
    alunos = serializers.StringRelatedField(many=True, read_only=True)
    professores = serializers.StringRelatedField(many=True, read_only=True)
    materias = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Classes
        fields = '__all__'
        # fields = ['id', 'nome', 'ano_letivo', 'alunos', 'professores', 'materias']


class AvaliacoesSerializer(serializers.ModelSerializer):
    # responsavel_por = serializers.StringRelatedField(read_only=True) # Exemplo para mostrar o nome do professor
    responsavel_por = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Avaliacoes
        fields = '__all__'
        # fields = ['id', 'nome', 'descricao', 'responsavel_por']

class NotasSerializer(serializers.ModelSerializer):
    # Usar StringRelatedField para mais detalhes
    aluno = serializers.StringRelatedField(read_only=True)
    avaliacao = serializers.StringRelatedField(read_only=True)
    atribuida_por = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Notas
        fields = '__all__'
        # fields = ['id', 'nota', 'aluno', 'avaliacao', 'atribuida_por', 'data_registro']


# Registro de Usuários

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de usuários com hashing para senhas.
    Usa os nomes de campo padrão do modelo User do Django: 'password', 'first_name', 'last_name'.
    """
    password = serializers.CharField(write_only=True, required=True, help_text="Letras, números e @/./+/-/_ somente.")
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)


    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'username': {'required': True},
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def create(self, validated_data):
        # Criação de um novo usuário
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

    def validate_username(self, value):
        # Username único
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username já existe.")
        return value
    

# --- Custom JWT Serializer ---
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customizes the JWT serializer to include user role and other details.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        # Determine the user's role based on linked profiles
        user_role = 'unknown' # Default role
        if hasattr(user, 'administracao_profile'):
            user_role = 'admin'
        elif hasattr(user, 'professor_profile'):
            user_role = 'teacher'
        elif hasattr(user, 'aluno_profile'):
            user_role = 'student'
        elif hasattr(user, 'responsavel_profile'):
            user_role = 'guardian'
        elif user.is_staff: # Fallback for Django staff users not linked to Administracao
            user_role = 'admin'

        token['user_id'] = user.id
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['user_role'] = user_role # Add the determined role

        return token

    def validate(self, attrs):
        # The default validate method authenticates the user and generates tokens.
        # It calls get_token() internally.
        data = super().validate(attrs)

        # After super().validate(), self.user will be set to the authenticated user.
        # We can now add the custom data to the response.
        # The custom claims are already added to the token by get_token,
        # but we also want them at the top level of the response for easier frontend access.

        # Determine the user's role based on linked profiles
        user_role = 'unknown' # Default role
        if hasattr(self.user, 'administracao_profile'):
            user_role = 'admin'
        elif hasattr(self.user, 'professor_profile'):
            user_role = 'teacher'
        elif hasattr(self.user, 'aluno_profile'):
            user_role = 'student'
        elif hasattr(self.user, 'responsavel_profile'):
            user_role = 'guardian'
        elif self.user.is_staff: # Fallback for Django staff users not linked to Administracao
            user_role = 'admin'


        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['first_name'] = self.user.first_name
        data['last_name'] = self.user.last_name
        data['user_role'] = user_role # Add the determined role to the response

        return data
