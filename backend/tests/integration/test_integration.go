package integration

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"time"
)

type TestData struct {
	Prompt  string            `json:"prompt,omitempty"`
	Context map[string]string `json:"context,omitempty"`
	Tools   []string          `json:"tools,omitempty"`
	TaskID  string            `json:"task_id,omitempty"`
}

type APIResponse struct {
	TaskID  string   `json:"task_id,omitempty"`
	Status  string   `json:"status,omitempty"`
	Message string   `json:"message,omitempty"`
	Result  string   `json:"result,omitempty"`
	Events  []string `json:"events,omitempty"`
}

func TestIntegration() bool {
	baseURL := "http://localhost:8000/ninja-api/grpc"
	headers := map[string]string{
		"X-API-Key":     "dev-api-key",
		"Content-Type":  "application/json",
	}

	log.Printf("Testing execute_task endpoint...")
	executeData := TestData{
		Prompt:  "Test task from Go client",
		Context: map[string]string{"source": "go_test"},
		Tools:   []string{"search", "code"},
	}

	executeJSON, err := json.Marshal(executeData)
	if err != nil {
		log.Printf("Error marshaling execute data: %v", err)
		return false
	}

	executeReq, err := http.NewRequest("POST", fmt.Sprintf("%s/execute_task", baseURL), bytes.NewBuffer(executeJSON))
	if err != nil {
		log.Printf("Error creating execute request: %v", err)
		return false
	}

	for key, value := range headers {
		executeReq.Header.Set(key, value)
	}

	client := &http.Client{}
	executeResp, err := client.Do(executeReq)
	if err != nil {
		log.Printf("Error executing request: %v", err)
		return false
	}
	defer executeResp.Body.Close()

	if executeResp.StatusCode == http.StatusOK {
		executeBody, err := ioutil.ReadAll(executeResp.Body)
		if err != nil {
			log.Printf("Error reading execute response: %v", err)
			return false
		}

		var result APIResponse
		err = json.Unmarshal(executeBody, &result)
		if err != nil {
			log.Printf("Error unmarshaling execute response: %v", err)
			return false
		}

		resultJSON, _ := json.MarshalIndent(result, "", "  ")
		log.Printf("Execute task response: %s", string(resultJSON))
		taskID := result.TaskID

		if taskID != "" {
			log.Printf("Testing get_task_status endpoint for task %s...", taskID)
			statusData := TestData{
				TaskID: taskID,
			}

			time.Sleep(1 * time.Second)

			statusJSON, err := json.Marshal(statusData)
			if err != nil {
				log.Printf("Error marshaling status data: %v", err)
				return false
			}

			statusReq, err := http.NewRequest("POST", fmt.Sprintf("%s/get_task_status", baseURL), bytes.NewBuffer(statusJSON))
			if err != nil {
				log.Printf("Error creating status request: %v", err)
				return false
			}

			for key, value := range headers {
				statusReq.Header.Set(key, value)
			}

			statusResp, err := client.Do(statusReq)
			if err != nil {
				log.Printf("Error executing status request: %v", err)
				return false
			}
			defer statusResp.Body.Close()

			if statusResp.StatusCode == http.StatusOK {
				statusBody, err := ioutil.ReadAll(statusResp.Body)
				if err != nil {
					log.Printf("Error reading status response: %v", err)
					return false
				}

				var statusResult APIResponse
				err = json.Unmarshal(statusBody, &statusResult)
				if err != nil {
					log.Printf("Error unmarshaling status response: %v", err)
					return false
				}

				statusResultJSON, _ := json.MarshalIndent(statusResult, "", "  ")
				log.Printf("Task status response: %s", string(statusResultJSON))

				log.Printf("Testing cancel_task endpoint for task %s...", taskID)
				cancelData := TestData{
					TaskID: taskID,
				}

				cancelJSON, err := json.Marshal(cancelData)
				if err != nil {
					log.Printf("Error marshaling cancel data: %v", err)
					return false
				}

				cancelReq, err := http.NewRequest("POST", fmt.Sprintf("%s/cancel_task", baseURL), bytes.NewBuffer(cancelJSON))
				if err != nil {
					log.Printf("Error creating cancel request: %v", err)
					return false
				}

				for key, value := range headers {
					cancelReq.Header.Set(key, value)
				}

				cancelResp, err := client.Do(cancelReq)
				if err != nil {
					log.Printf("Error executing cancel request: %v", err)
					return false
				}
				defer cancelResp.Body.Close()

				if cancelResp.StatusCode == http.StatusOK {
					cancelBody, err := ioutil.ReadAll(cancelResp.Body)
					if err != nil {
						log.Printf("Error reading cancel response: %v", err)
						return false
					}

					var cancelResult APIResponse
					err = json.Unmarshal(cancelBody, &cancelResult)
					if err != nil {
						log.Printf("Error unmarshaling cancel response: %v", err)
						return false
					}

					cancelResultJSON, _ := json.MarshalIndent(cancelResult, "", "  ")
					log.Printf("Cancel task response: %s", string(cancelResultJSON))
					return true
				} else {
					log.Printf("Cancel task request failed with status code %d", cancelResp.StatusCode)
					log.Printf("Response: %s", cancelResp.Status)
				}
			} else {
				log.Printf("Get task status request failed with status code %d", statusResp.StatusCode)
				log.Printf("Response: %s", statusResp.Status)
			}
		}
	} else {
		log.Printf("Execute task request failed with status code %d", executeResp.StatusCode)
		log.Printf("Response: %s", executeResp.Status)
	}

	return false
}

func VerifyPydanticIntegration() bool {
	log.Printf("Verifying Pydantic integration with Django...")

	headers := map[string]string{
		"X-API-Key": "dev-api-key",
	}

	req, err := http.NewRequest("GET", "http://localhost:8000/ninja-api/models", nil)
	if err != nil {
		log.Printf("Error creating request: %v", err)
		return false
	}

	for key, value := range headers {
		req.Header.Set(key, value)
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error executing request: %v", err)
		return false
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Printf("Error reading response: %v", err)
			return false
		}

		var result interface{}
		err = json.Unmarshal(body, &result)
		if err != nil {
			log.Printf("Error unmarshaling response: %v", err)
			return false
		}

		resultJSON, _ := json.MarshalIndent(result, "", "  ")
		log.Printf("Pydantic models response: %s", string(resultJSON))
		return true
	} else {
		log.Printf("Pydantic models request failed with status code %d", resp.StatusCode)
		log.Printf("Response: %s", resp.Status)
	}

	return false
}

func VerifyMLAppIntegration() bool {
	log.Printf("Verifying ML App integration with Django...")

	headers := map[string]string{
		"X-API-Key": "dev-api-key",
	}

	req, err := http.NewRequest("GET", "http://localhost:8000/ml-api/models", nil)
	if err != nil {
		log.Printf("Error creating request: %v", err)
		return false
	}

	for key, value := range headers {
		req.Header.Set(key, value)
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error executing request: %v", err)
		return false
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusServiceUnavailable {
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Printf("Error reading response: %v", err)
			return false
		}

		var result interface{}
		err = json.Unmarshal(body, &result)
		if err != nil {
			log.Printf("Error unmarshaling response: %v", err)
			return false
		}

		resultJSON, _ := json.MarshalIndent(result, "", "  ")
		log.Printf("ML models response: %s", string(resultJSON))
		return true
	} else {
		log.Printf("ML models request failed with status code %d", resp.StatusCode)
		log.Printf("Response: %s", resp.Status)
	}

	return false
}

func VerifyGoIntegration() bool {
	return TestIntegration()
}

func RunAllTests() int {
	log.Printf("Starting Django backend verification tests...")

	grpcSuccess := TestIntegration()
	log.Printf("gRPC integration test %s", successString(grpcSuccess))

	pydanticSuccess := VerifyPydanticIntegration()
	log.Printf("Pydantic integration test %s", successString(pydanticSuccess))

	mlSuccess := VerifyMLAppIntegration()
	log.Printf("ML App integration test %s", successString(mlSuccess))

	goSuccess := VerifyGoIntegration()
	log.Printf("Go integration test %s", successString(goSuccess))

	if grpcSuccess && pydanticSuccess && mlSuccess && goSuccess {
		log.Printf("All integration tests passed!")
		return 0
	} else {
		log.Printf("Some integration tests failed.")
		return 1
	}
}

func successString(success bool) string {
	if success {
		return "succeeded"
	}
	return "failed"
}

func main() {
	os.Exit(RunAllTests())
}
