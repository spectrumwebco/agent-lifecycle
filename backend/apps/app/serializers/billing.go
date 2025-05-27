package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type PlanSerializer struct {
	core.Serializer
}

func NewPlanSerializer() *PlanSerializer {
	serializer := &PlanSerializer{
		Serializer: core.NewSerializer("Plan"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "plan_type", "price", "currency",
		"billing_cycle", "features", "token_limit", "user_limit",
		"workspace_limit", "is_active", "is_public", "subscriptions_count",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "subscriptions_count",
	})
	
	serializer.AddMethodField("subscriptions_count", "GetSubscriptionsCount")

	return serializer
}

func (s *PlanSerializer) GetSubscriptionsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "subscriptions.count")
}

type SubscriptionSerializer struct {
	core.Serializer
}

func NewSubscriptionSerializer() *SubscriptionSerializer {
	serializer := &SubscriptionSerializer{
		Serializer: core.NewSerializer("Subscription"),
	}

	serializer.SetFields([]string{
		"id", "organization", "organization_name", "plan", "plan_name",
		"external_id", "status", "start_date", "end_date", "trial_end_date",
		"canceled_at", "custom_price", "metadata", "invoices_count",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
		"plan_name", "invoices_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("plan_name", "plan.name")
	serializer.AddMethodField("invoices_count", "GetInvoicesCount")

	return serializer
}

func (s *SubscriptionSerializer) GetInvoicesCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "invoices.count")
}

type InvoiceSerializer struct {
	core.Serializer
}

func NewInvoiceSerializer() *InvoiceSerializer {
	serializer := &InvoiceSerializer{
		Serializer: core.NewSerializer("Invoice"),
	}

	serializer.SetFields([]string{
		"id", "organization", "organization_name", "subscription", "subscription_id",
		"invoice_number", "external_id", "amount", "tax_amount", "total_amount",
		"currency", "status", "issue_date", "due_date", "paid_date",
		"line_items", "metadata", "payments_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
		"subscription_id", "payments_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("subscription_id", "subscription.id")
	serializer.AddMethodField("payments_count", "GetPaymentsCount")

	return serializer
}

func (s *InvoiceSerializer) GetPaymentsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "payments.count")
}

type PaymentSerializer struct {
	core.Serializer
}

func NewPaymentSerializer() *PaymentSerializer {
	serializer := &PaymentSerializer{
		Serializer: core.NewSerializer("Payment"),
	}

	serializer.SetFields([]string{
		"id", "organization", "organization_name", "invoice", "invoice_number",
		"transaction_id", "external_id", "amount", "currency", "payment_method",
		"status", "payment_date", "error_code", "error_message", "metadata",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "invoice_number",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("invoice_number", "invoice.invoice_number")

	return serializer
}

type UsageSerializer struct {
	core.Serializer
}

func NewUsageSerializer() *UsageSerializer {
	serializer := &UsageSerializer{
		Serializer: core.NewSerializer("Usage"),
	}

	serializer.SetFields([]string{
		"id", "organization", "organization_name", "subscription", "subscription_id",
		"resource_type", "quantity", "unit_price", "currency", "start_date",
		"end_date", "metadata", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "subscription_id",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("subscription_id", "subscription.id")

	return serializer
}

func init() {
	core.RegisterSerializer("PlanSerializer", NewPlanSerializer())
	core.RegisterSerializer("SubscriptionSerializer", NewSubscriptionSerializer())
	core.RegisterSerializer("InvoiceSerializer", NewInvoiceSerializer())
	core.RegisterSerializer("PaymentSerializer", NewPaymentSerializer())
	core.RegisterSerializer("UsageSerializer", NewUsageSerializer())
}
