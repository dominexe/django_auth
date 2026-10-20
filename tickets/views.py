from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import Category, Ticket
from .serializers import CategorySerializer, TicketSerializer


class TicketsLoginView(LoginView):
    template_name = "tickets/login.html"
    next_page = reverse_lazy("tickets:dashboard")
    redirect_authenticated_user = True


@login_required(login_url="tickets:login")
@ensure_csrf_cookie
def dashboard(request):
    return render(request, "tickets/dashboard.html")


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    pagination_class = None


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    pagination_class = None

    def get_queryset(self):
        queryset = (
            Ticket.objects
            .filter(owner=self.request.user)
            .select_related("category")
        )

        # Фильтр относится только к списку, а не к отдельному объекту.
        if self.action == "list":
            status = self.request.query_params.get("status")

            if status:
                if status not in Ticket.Status.values:
                    raise ValidationError({
                        "status": "Неизвестный статус.",
                    })

                queryset = queryset.filter(status=status)

        return queryset.order_by("-created_at", "-id")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)