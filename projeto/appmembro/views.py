from __future__ import unicode_literals


from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView

from django.http import HttpResponse
from django.template.loader import render_to_string
#from weasyprint import HTML

from mail_templated import EmailMessage

from utils.decorators import LoginRequiredMixin, MembroRequiredMixin

from aviso.models import Aviso
from evento.models import Evento
from frequencia.models import Frequencia
from inscricao.models import Inscricao
from usuario.models import Usuario

from .forms import MembroCreateForm, InscricaoForm, FrequenciaForm
from evento.forms import BuscaEventoForm
# from inscricao.forms import BuscaInscricaoForm


class HomeView(LoginRequiredMixin, MembroRequiredMixin, TemplateView):
    template_name = 'appmembro/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['avisos'] = Aviso.ativos.filter(destinatario__in=[self.request.user.tipo, 'TODOS'])[0:2]
        return context

class AboutView(LoginRequiredMixin, MembroRequiredMixin, TemplateView):
    template_name = 'appmembro/about.html'
    

class DadosMembroUpdateView(LoginRequiredMixin, MembroRequiredMixin, UpdateView):
    model = Usuario
    template_name = 'appmembro/dados_membro_form.html'
    form_class = MembroCreateForm  
    
    success_url = 'appmembro_home'

    def get_object(self, queryset=None):
        return self.request.user
     
    def get_success_url(self):
        messages.success(self.request, 'Seus dados foram alterados com sucesso!')
        return reverse(self.success_url)

class EventoListView(LoginRequiredMixin, MembroRequiredMixin, ListView):
    model = Evento
    template_name = 'appmembro/evento_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET:
            #quando ja tem dados filtrando
            context['form'] = BuscaEventoForm(data=self.request.GET)
        else:
            #quando acessa sem dados filtrando
            context['form'] = BuscaEventoForm()
        return context

    def get_queryset(self):                
        qs = super().get_queryset().filter(is_active=True)
        
        if self.request.GET:
            #quando ja tem dados filtrando
            form = BuscaEventoForm(data=self.request.GET)
        else:
            #quando acessa sem dados filtrando
            form = BuscaEventoForm()

        if form.is_valid():            
            pesquisa = form.cleaned_data.get('pesquisa')            
                        
            if pesquisa:
                qs = qs.filter(Q(nome__icontains=pesquisa) | Q(coordenador__nome__icontains=pesquisa) | Q(instituicao__nome__icontains=pesquisa) | Q(instituicao__sigla__icontains=pesquisa) | Q(descricao__icontains=pesquisa))   
            
        return qs


class InscricaoListView(LoginRequiredMixin, MembroRequiredMixin, ListView):
    model = Inscricao
    template_name = 'appmembro/inscricao_list.html'
   
    def get_queryset(self):
        queryset = super(InscricaoListView, self).get_queryset()
        return queryset.filter(participante = self.request.user)
    
    
class InscricaoCreateView(LoginRequiredMixin, MembroRequiredMixin, CreateView):
    model = Inscricao
    template_name = 'appmembro/inscricao_form.html'
    form_class = InscricaoForm
    success_url = 'appmembro_evento_list'
    
    def get_initial(self):
        initials = super().get_initial()
        initials['usuario'] = Usuario.objects.get(slug=self.request.user.slug)
        initials['evento'] = Evento.objects.get(slug=self.request.GET.get('evento_slug'))
        return initials

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento'] = Evento.objects.get(slug=self.request.GET.get('evento_slug'))
        return context

    def form_valid(self, form):
        try:
            formulario = form.save(commit=False)

            formulario.participante = self.request.user
            formulario.evento = Evento.objects.get(slug=self.request.GET.get('evento_slug'))
            
            if formulario.evento.quantidade_vagas <= 0:
                messages.error(self.request,"Não há mais vagas para este evento. Inscrição NÃO realizada. Aguarde liberar uma vaga!!!")  
                return super().form_invalid(form)
            
            formulario.save()
            
            try:
                """ enviar e-mail para participante """
                if not formulario.participante.email:
                    raise
                message = EmailMessage('usuario/email/inscricao_participante.html', {'inscricao': formulario, 'site': settings.DOMINIO_URL},
                        settings.EMAIL_HOST_USER, to=[formulario.participante.email])
                message.send()
            except Exception as e:
                # alterar para outro tipo de requisição http
                # messages.warning(self.request, f"SEM NOTIFICAÇÃO POR EMAIL AO PARTICIPANTE!! Erro: {e}")
                messages.warning(self.request, f"SEM NOTIFICAÇÃO POR EMAIL AO PARTICIPANTE!!")

            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, 'Erro ao inscrever-se no evento. Verifique se você já não está inscrito neste evento!')
            return super().form_invalid(form)
    
    def get_success_url(self):
        messages.success(self.request, 'Inscrição realizada com sucesso na plataforma!')
        return reverse(self.success_url)
    

class InscricaoDeleteView(LoginRequiredMixin, MembroRequiredMixin, DeleteView):
    model = Inscricao
    template_name = 'appmembro/inscricao_confirm_delete.html'
    success_url = 'appmembro_inscricao_list'
    
    def get_success_url(self):
        messages.success(self.request, 'Inscrição, para o evento, removida com sucesso na plataforma!')
        return reverse(self.success_url)

    def post(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL. If the object is protected, send an error message.
        """
        try:
            self.object = self.get_object()
            self.object.delete()
        except Exception as e:
            messages.error(request, f'Há dependências ligadas à essa Inscrição, permissão negada!')
        return redirect(self.success_url)
    
    
class FrequenciaCreateView(LoginRequiredMixin, MembroRequiredMixin, CreateView):
    model = Frequencia
    template_name = 'appmembro/frequencia_form.html'
    # fields = ['inscricao','codigo_frequencia']
    form_class = FrequenciaForm
    success_url = 'appmembro_inscricao_list'
    
    def get_initial(self):
        initials = super().get_initial()
        initials['inscricao'] = Inscricao.objects.get(slug=self.request.GET.get('inscricao_slug'))
        return initials

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inscricao'] = Inscricao.objects.get(slug=self.request.GET.get('inscricao_slug'))
        return context

    def form_valid(self, form):
        try:
            formulario = form.save(commit=False)
            formulario.inscricao = Inscricao.objects.get(slug=self.request.GET.get('inscricao_slug'))
            
            if formulario.inscricao.evento.codigo_frequencia != formulario.codigo_frequencia:
                messages.error(self.request, 'Código de frequência inválido. Verifique o código informado!')
                return super().form_invalid(form)
            
            formulario.save()

            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, 'Erro ao registrar frequência. Verifique se você já não realizaou a frequência neste evento!')
            return super().form_invalid(form)
    
    def get_success_url(self):
        messages.success(self.request, 'Frequência realizada com sucesso na plataforma!')
        return reverse(self.success_url)
    
    
class InscricaoPdfView(LoginRequiredMixin, DetailView):
    model = Inscricao
    template_name = 'appmembro/impressoes/atestado_pdf.html'
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        html_string = render_to_string(self.template_name, context)
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="atestado.pdf"'
        return response


class InscricaoDetailView(LoginRequiredMixin, DetailView):
    model = Inscricao
    template_name = 'appmembro/inscricao_detail.html'