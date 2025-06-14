# Generated by Django 4.2.21 on 2025-06-02 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inscricao', '0005_alter_inscricao_participante'),
        ('frequencia', '0005_frequencia_codigo_frequencia'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='frequencia',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='frequencia',
            name='codigo_frequencia',
            field=models.CharField(blank=True, help_text='Use o código de frequência informado pela organização do evento.', max_length=20, null=True, verbose_name='Código de frequência'),
        ),
        migrations.AlterUniqueTogether(
            name='frequencia',
            unique_together={('inscricao', 'codigo_frequencia')},
        ),
    ]
