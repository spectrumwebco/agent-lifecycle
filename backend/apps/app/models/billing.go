package models

import (
	"time"

	"github.com/google/uuid"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type Plan struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	Name           string     `json:"name" gorm:"size:255;not null"`
	Description    string     `json:"description" gorm:"type:text"`
	PlanType       string     `json:"plan_type" gorm:"size:20;not null;default:'free'"`
	Price          float64    `json:"price" gorm:"type:decimal(10,2);default:0.00"`
	Currency       string     `json:"currency" gorm:"size:3;not null;default:'USD'"`
	BillingCycle   string     `json:"billing_cycle" gorm:"size:20;not null;default:'monthly'"`
	Features       db.JSONMap `json:"features" gorm:"type:jsonb;default:'{}'"`
	TokenLimit     int        `json:"token_limit" gorm:"default:0"`
	UserLimit      int        `json:"user_limit" gorm:"default:1"`
	WorkspaceLimit int        `json:"workspace_limit" gorm:"default:1"`
	IsActive       bool       `json:"is_active" gorm:"default:true"`
	IsPublic       bool       `json:"is_public" gorm:"default:true"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	PlanTypeFree         = "free"
	PlanTypeStarter      = "starter"
	PlanTypeProfessional = "professional"
	PlanTypeEnterprise   = "enterprise"
	PlanTypeCustom       = "custom"
)

const (
	BillingCycleMonthly   = "monthly"
	BillingCycleQuarterly = "quarterly"
	BillingCycleAnnual    = "annual"
	BillingCycleCustom    = "custom"
)

func (Plan) TableName() string {
	return "app_plan"
}

func (p Plan) String() string {
	return p.Name + " (" + p.PlanType + ") - " + string(p.Price) + " " + p.Currency + "/" + p.BillingCycle
}

type Subscription struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	PlanID         uuid.UUID  `json:"plan_id" gorm:"type:uuid;not null"`
	ExternalID     string     `json:"external_id" gorm:"size:255"`
	Status         string     `json:"status" gorm:"size:20;not null;default:'active'"`
	StartDate      time.Time  `json:"start_date" gorm:"not null"`
	EndDate        *time.Time `json:"end_date"`
	TrialEndDate   *time.Time `json:"trial_end_date"`
	CanceledAt     *time.Time `json:"canceled_at"`
	CustomPrice    *float64   `json:"custom_price" gorm:"type:decimal(10,2)"`
	Metadata       db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	SubscriptionStatusActive   = "active"
	SubscriptionStatusTrialing = "trialing"
	SubscriptionStatusPastDue  = "past_due"
	SubscriptionStatusCanceled = "canceled"
	SubscriptionStatusUnpaid   = "unpaid"
)

func (Subscription) TableName() string {
	return "app_subscription"
}

func (s Subscription) String() string {
	return "Subscription"
}

type Invoice struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	SubscriptionID *uuid.UUID `json:"subscription_id" gorm:"type:uuid"`
	InvoiceNumber  string     `json:"invoice_number" gorm:"size:50;uniqueIndex;not null"`
	ExternalID     string     `json:"external_id" gorm:"size:255"`
	Amount         float64    `json:"amount" gorm:"type:decimal(10,2);not null"`
	TaxAmount      float64    `json:"tax_amount" gorm:"type:decimal(10,2);default:0.00"`
	TotalAmount    float64    `json:"total_amount" gorm:"type:decimal(10,2);not null"`
	Currency       string     `json:"currency" gorm:"size:3;not null;default:'USD'"`
	Status         string     `json:"status" gorm:"size:20;not null;default:'draft'"`
	IssueDate      time.Time  `json:"issue_date" gorm:"not null"`
	DueDate        time.Time  `json:"due_date" gorm:"not null"`
	PaidDate       *time.Time `json:"paid_date"`
	LineItems      db.JSONMap `json:"line_items" gorm:"type:jsonb;default:'[]'"`
	Metadata       db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	InvoiceStatusDraft         = "draft"
	InvoiceStatusOpen          = "open"
	InvoiceStatusPaid          = "paid"
	InvoiceStatusUncollectible = "uncollectible"
	InvoiceStatusVoid          = "void"
)

func (Invoice) TableName() string {
	return "app_invoice"
}

func (i Invoice) String() string {
	return "Invoice " + i.InvoiceNumber
}

type Payment struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	InvoiceID      *uuid.UUID `json:"invoice_id" gorm:"type:uuid"`
	TransactionID  string     `json:"transaction_id" gorm:"size:255;uniqueIndex;not null"`
	ExternalID     string     `json:"external_id" gorm:"size:255"`
	Amount         float64    `json:"amount" gorm:"type:decimal(10,2);not null"`
	Currency       string     `json:"currency" gorm:"size:3;not null;default:'USD'"`
	PaymentMethod  string     `json:"payment_method" gorm:"size:20;not null;default:'credit_card'"`
	Status         string     `json:"status" gorm:"size:20;not null;default:'pending'"`
	PaymentDate    time.Time  `json:"payment_date" gorm:"not null"`
	ErrorCode      string     `json:"error_code" gorm:"size:100"`
	ErrorMessage   string     `json:"error_message" gorm:"type:text"`
	Metadata       db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	PaymentMethodCreditCard    = "credit_card"
	PaymentMethodBankTransfer  = "bank_transfer"
	PaymentMethodPayPal        = "paypal"
	PaymentMethodCrypto        = "crypto"
	PaymentMethodOther         = "other"
)

const (
	PaymentStatusPending           = "pending"
	PaymentStatusCompleted         = "completed"
	PaymentStatusFailed            = "failed"
	PaymentStatusRefunded          = "refunded"
	PaymentStatusPartiallyRefunded = "partially_refunded"
)

func (Payment) TableName() string {
	return "app_payment"
}

func (p Payment) String() string {
	return "Payment " + p.TransactionID
}

type Usage struct {
	ID             uuid.UUID  `json:"id" gorm:"primaryKey;type:uuid;default:uuid_generate_v4()"`
	OrganizationID uuid.UUID  `json:"organization_id" gorm:"type:uuid;not null"`
	SubscriptionID *uuid.UUID `json:"subscription_id" gorm:"type:uuid"`
	ResourceType   string     `json:"resource_type" gorm:"size:20;not null;default:'tokens'"`
	Quantity       int64      `json:"quantity" gorm:"not null"`
	UnitPrice      float64    `json:"unit_price" gorm:"type:decimal(10,6);default:0.000000"`
	Currency       string     `json:"currency" gorm:"size:3;not null;default:'USD'"`
	StartDate      time.Time  `json:"start_date" gorm:"not null"`
	EndDate        time.Time  `json:"end_date" gorm:"not null"`
	Metadata       db.JSONMap `json:"metadata" gorm:"type:jsonb;default:'{}'"`
	CreatedAt      time.Time  `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt      time.Time  `json:"updated_at" gorm:"autoUpdateTime"`
}

const (
	UsageTypeTokens   = "tokens"
	UsageTypeStorage  = "storage"
	UsageTypeAPICalls = "api_calls"
	UsageTypeSessions = "sessions"
	UsageTypeUsers    = "users"
)

func (Usage) TableName() string {
	return "app_usage"
}

func (u Usage) String() string {
	return "Usage Record"
}

func init() {
	db.RegisterModel("Plan", Plan{})
	db.RegisterModel("Subscription", Subscription{})
	db.RegisterModel("Invoice", Invoice{})
	db.RegisterModel("Payment", Payment{})
	db.RegisterModel("Usage", Usage{})
}
