from rest_framework import serializers
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