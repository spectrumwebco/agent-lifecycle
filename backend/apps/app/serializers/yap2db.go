package serializers

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type DatabaseConnectionSerializer struct {
	core.Serializer
}

func NewDatabaseConnectionSerializer() *DatabaseConnectionSerializer {
	serializer := &DatabaseConnectionSerializer{
		Serializer: core.NewSerializer("DatabaseConnection"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "organization", "organization_name",
		"db_type", "host", "port", "database", "username", "connection_string",
		"ssl_enabled", "status", "last_connected_at", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "last_connected_at",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	
	serializer.SetWriteOnlyFields([]string{
		"password", "connection_string",
	})

	return serializer
}

type SavedQuerySerializer struct {
	core.Serializer
}

func NewSavedQuerySerializer() *SavedQuerySerializer {
	serializer := &SavedQuerySerializer{
		Serializer: core.NewSerializer("SavedQuery"),
	}

	serializer.SetFields([]string{
		"id", "name", "description", "organization", "organization_name",
		"connection", "connection_name", "query_text", "parameters",
		"is_parameterized", "created_by", "created_by_username",
		"executions_count", "created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name",
		"connection_name", "created_by_username", "executions_count",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("connection_name", "connection.name")
	serializer.AddReadOnlyField("created_by_username", "created_by.username")
	serializer.AddMethodField("executions_count", "GetExecutionsCount")

	return serializer
}

func (s *SavedQuerySerializer) GetExecutionsCount(obj interface{}) (interface{}, error) {
	return core.CallObjectMethod(obj, "executions.count")
}

type QueryExecutionSerializer struct {
	core.Serializer
}

func NewQueryExecutionSerializer() *QueryExecutionSerializer {
	serializer := &QueryExecutionSerializer{
		Serializer: core.NewSerializer("QueryExecution"),
	}

	serializer.SetFields([]string{
		"id", "organization", "organization_name", "connection", "connection_name",
		"saved_query", "saved_query_name", "query_text", "parameters",
		"status", "start_time", "end_time", "duration", "rows_affected",
		"error_message", "executed_by", "executed_by_username",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "organization_name", "connection_name",
		"saved_query_name", "executed_by_username", "start_time", "end_time",
		"duration", "rows_affected", "error_message",
	})
	
	serializer.AddReadOnlyField("organization_name", "organization.name")
	serializer.AddReadOnlyField("connection_name", "connection.name")
	serializer.AddReadOnlyField("saved_query_name", "saved_query.name")
	serializer.AddReadOnlyField("executed_by_username", "executed_by.username")

	return serializer
}

type QueryResultSerializer struct {
	core.Serializer
}

func NewQueryResultSerializer() *QueryResultSerializer {
	serializer := &QueryResultSerializer{
		Serializer: core.NewSerializer("QueryResult"),
	}

	serializer.SetFields([]string{
		"id", "execution", "execution_id", "result_data",
		"column_names", "column_types", "row_count",
		"created_at", "updated_at",
	})
	
	serializer.SetReadOnlyFields([]string{
		"id", "created_at", "updated_at", "execution_id",
		"column_names", "column_types", "row_count",
	})
	
	serializer.AddReadOnlyField("execution_id", "execution.id")

	return serializer
}

func init() {
	core.RegisterSerializer("DatabaseConnectionSerializer", NewDatabaseConnectionSerializer())
	core.RegisterSerializer("SavedQuerySerializer", NewSavedQuerySerializer())
	core.RegisterSerializer("QueryExecutionSerializer", NewQueryExecutionSerializer())
	core.RegisterSerializer("QueryResultSerializer", NewQueryResultSerializer())
}
