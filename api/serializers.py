from rest_framework import serializers
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
    class Meta:
        model = Classes
        fields = '__all__'
        # fields = ['id', 'nome', 'ano_letivo', 'alunos', 'professores', 'materias']


class AvaliacoesSerializer(serializers.ModelSerializer):
    # responsavel_por = serializers.StringRelatedField(read_only=True) # Exemplo para mostrar o nome do professor
    class Meta:
        model = Avaliacoes
        fields = '__all__'
        # fields = ['id', 'nome', 'descricao', 'responsavel_por']

class NotasSerializer(serializers.ModelSerializer):
    # Usar StringRelatedField para mais detalhes
    # aluno = serializers.StringRelatedField(read_only=True)
    # avaliacao = serializers.StringRelatedField(read_only=True)
    # atribuida_por = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Notas
        fields = '__all__'
        # fields = ['id', 'nota', 'aluno', 'avaliacao', 'atribuida_por', 'data_registro']
