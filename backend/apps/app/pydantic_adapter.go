package app

import (
	"encoding/json"
	"net/http"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type PydanticModelAdapter struct{}

func (a *PydanticModelAdapter) ToDict(model interface{}) (map[string]interface{}, error) {
	pyModel, err := core.GoToPyObject(model)
	if err != nil {
		return nil, err
	}

	modelDump, err := core.CallPyObjectMethod(pyModel, "model_dump")
	if err != nil {
		return nil, err
	}

	result, err := core.PyObjectToMap(modelDump)
	if err != nil {
		return nil, err
	}

	return result, nil
}

func (a *PydanticModelAdapter) FromDict(modelClass interface{}, data map[string]interface{}) (interface{}, error) {
	pyData, err := core.MapToPyObject(data)
	if err != nil {
		return nil, err
	}

	result, err := core.CallPyObjectConstructor(modelClass, pyData)
	if err != nil {
		return nil, err
	}

	return result, nil
}

func (a *PydanticModelAdapter) ToListOfDicts(models []interface{}) ([]map[string]interface{}, error) {
	result := make([]map[string]interface{}, 0, len(models))

	for _, model := range models {
		dict, err := a.ToDict(model)
		if err != nil {
			return nil, err
		}
		result = append(result, dict)
	}

	return result, nil
}

func (a *PydanticModelAdapter) FromListOfDicts(modelClass interface{}, dataList []map[string]interface{}) ([]interface{}, error) {
	result := make([]interface{}, 0, len(dataList))

	for _, data := range dataList {
		model, err := a.FromDict(modelClass, data)
		if err != nil {
			return nil, err
		}
		result = append(result, model)
	}

	return result, nil
}

type DjangoToPydanticMiddleware struct {
	Next http.Handler
}

func NewDjangoToPydanticMiddleware(next http.Handler) *DjangoToPydanticMiddleware {
	return &DjangoToPydanticMiddleware{
		Next: next,
	}
}

func (m *DjangoToPydanticMiddleware) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	m.Next.ServeHTTP(w, r)
}

func PydanticToDjango(model interface{}) (map[string]interface{}, error) {
	adapter := &PydanticModelAdapter{}
	return adapter.ToDict(model)
}

func DjangoToPydantic(modelClass interface{}, data map[string]interface{}) (interface{}, error) {
	adapter := &PydanticModelAdapter{}
	return adapter.FromDict(modelClass, data)
}

func init() {
	core.RegisterMiddleware("DjangoToPydanticMiddleware", func(next http.Handler) http.Handler {
		return NewDjangoToPydanticMiddleware(next)
	})
}
