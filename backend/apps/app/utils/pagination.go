package utils

import (
	"net/url"
	"strconv"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/api"
)

type StandardResultsSetPagination struct {
	api.BasePagination
	PageSize     int
	PageSizeParam string
	MaxPageSize  int
	Page         *api.Page
}

func NewStandardResultsSetPagination() *StandardResultsSetPagination {
	return &StandardResultsSetPagination{
		BasePagination: api.NewBasePagination(),
		PageSize:       25,
		PageSizeParam:  "page_size",
		MaxPageSize:    100,
	}
}

func (p *StandardResultsSetPagination) GetPageSize(request *core.Request) int {
	if p.PageSizeParam != "" {
		sizeStr := request.GetQueryParam(p.PageSizeParam)
		if sizeStr != "" {
			size, err := strconv.Atoi(sizeStr)
			if err == nil && size > 0 {
				if p.MaxPageSize > 0 && size > p.MaxPageSize {
					return p.MaxPageSize
				}
				return size
			}
		}
	}
	return p.PageSize
}

func (p *StandardResultsSetPagination) GetNextLink() string {
	if p.Page == nil || p.Page.Number >= p.Page.Paginator.NumPages {
		return ""
	}
	
	return p.BuildLink(p.Page.Number + 1)
}

func (p *StandardResultsSetPagination) GetPreviousLink() string {
	if p.Page == nil || p.Page.Number <= 1 {
		return ""
	}
	
	return p.BuildLink(p.Page.Number - 1)
}

func (p *StandardResultsSetPagination) BuildLink(pageNumber int) string {
	if p.Request == nil {
		return ""
	}
	
	uri, err := url.Parse(p.Request.URL)
	if err != nil {
		return ""
	}
	
	query := uri.Query()
	query.Set("page", strconv.Itoa(pageNumber))
	
	if p.PageSizeParam != "" && p.GetPageSize(p.Request) != p.PageSize {
		query.Set(p.PageSizeParam, strconv.Itoa(p.GetPageSize(p.Request)))
	}
	
	uri.RawQuery = query.Encode()
	return uri.String()
}

func (p *StandardResultsSetPagination) GetPaginatedResponse(data interface{}) *api.Response {
	if p.Page == nil {
		return api.NewResponse(data)
	}
	
	return api.NewResponse(map[string]interface{}{
		"count":        p.Page.Paginator.Count,
		"next":         p.GetNextLink(),
		"previous":     p.GetPreviousLink(),
		"page_size":    p.GetPageSize(p.Request),
		"current_page": p.Page.Number,
		"total_pages":  p.Page.Paginator.NumPages,
		"results":      data,
	})
}

func (p *StandardResultsSetPagination) Paginate(request *core.Request, queryset interface{}) (interface{}, error) {
	p.Request = request
	pageSize := p.GetPageSize(request)
	
	pageStr := request.GetQueryParam("page")
	page := 1
	if pageStr != "" {
		pageNum, err := strconv.Atoi(pageStr)
		if err == nil && pageNum > 0 {
			page = pageNum
		}
	}
	
	result, err := core.CallPythonFunction("django.core.paginator", "Paginator", []interface{}{queryset, pageSize})
	if err != nil {
		return nil, err
	}
	
	pageObj, err := core.CallMethod(result, "page", []interface{}{page})
	if err != nil {
		if page > 1 {
			return p.Paginate(request, queryset)
		}
		return nil, err
	}
	
	p.Page = &api.Page{
		Number: page,
		Paginator: &api.Paginator{
			Count:    core.GetAttrInt(result, "count"),
			NumPages: core.GetAttrInt(result, "num_pages"),
		},
	}
	
	return core.GetAttr(pageObj, "object_list"), nil
}

type LargeResultsSetPagination struct {
	StandardResultsSetPagination
}

func NewLargeResultsSetPagination() *LargeResultsSetPagination {
	return &LargeResultsSetPagination{
		StandardResultsSetPagination: *NewStandardResultsSetPagination(),
	}
}

func (p *LargeResultsSetPagination) Initialize() {
	p.PageSize = 100
	p.PageSizeParam = "page_size"
	p.MaxPageSize = 1000
}

type CustomLimitOffsetPagination struct {
	api.BasePagination
	DefaultLimit int
	MaxLimit     int
	LimitParam   string
	OffsetParam  string
	Count        int
	Limit        int
	Offset       int
}

func NewCustomLimitOffsetPagination() *CustomLimitOffsetPagination {
	p := &CustomLimitOffsetPagination{
		BasePagination: api.NewBasePagination(),
		DefaultLimit:   25,
		MaxLimit:       100,
		LimitParam:     "limit",
		OffsetParam:    "offset",
	}
	return p
}

func (p *CustomLimitOffsetPagination) GetLimit(request *core.Request) int {
	if p.LimitParam == "" {
		return p.DefaultLimit
	}
	
	limitStr := request.GetQueryParam(p.LimitParam)
	if limitStr == "" {
		return p.DefaultLimit
	}
	
	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit <= 0 {
		return p.DefaultLimit
	}
	
	if p.MaxLimit > 0 && limit > p.MaxLimit {
		return p.MaxLimit
	}
	
	return limit
}

func (p *CustomLimitOffsetPagination) GetOffset(request *core.Request) int {
	if p.OffsetParam == "" {
		return 0
	}
	
	offsetStr := request.GetQueryParam(p.OffsetParam)
	if offsetStr == "" {
		return 0
	}
	
	offset, err := strconv.Atoi(offsetStr)
	if err != nil || offset < 0 {
		return 0
	}
	
	return offset
}

func (p *CustomLimitOffsetPagination) GetNextLink() string {
	if p.Offset + p.Limit >= p.Count {
		return ""
	}
	
	return p.BuildLink(p.Limit, p.Offset + p.Limit)
}

func (p *CustomLimitOffsetPagination) GetPreviousLink() string {
	if p.Offset <= 0 {
		return ""
	}
	
	previousOffset := p.Offset - p.Limit
	if previousOffset < 0 {
		previousOffset = 0
	}
	
	return p.BuildLink(p.Limit, previousOffset)
}

func (p *CustomLimitOffsetPagination) BuildLink(limit, offset int) string {
	if p.Request == nil {
		return ""
	}
	
	uri, err := url.Parse(p.Request.URL)
	if err != nil {
		return ""
	}
	
	query := uri.Query()
	query.Set(p.LimitParam, strconv.Itoa(limit))
	query.Set(p.OffsetParam, strconv.Itoa(offset))
	
	uri.RawQuery = query.Encode()
	return uri.String()
}

func (p *CustomLimitOffsetPagination) GetPaginatedResponse(data interface{}) *api.Response {
	return api.NewResponse(map[string]interface{}{
		"count":    p.Count,
		"next":     p.GetNextLink(),
		"previous": p.GetPreviousLink(),
		"limit":    p.Limit,
		"offset":   p.Offset,
		"results":  data,
	})
}

func (p *CustomLimitOffsetPagination) Paginate(request *core.Request, queryset interface{}) (interface{}, error) {
	p.Request = request
	p.Limit = p.GetLimit(request)
	p.Offset = p.GetOffset(request)
	
	count, err := core.CallPythonFunction("django.db.models", "QuerySet.count", []interface{}{queryset})
	if err != nil {
		return nil, err
	}
	p.Count = count.(int)
	
	result, err := core.CallPythonFunction("django.db.models", "QuerySet.all", []interface{}{queryset})
	if err != nil {
		return nil, err
	}
	
	sliced, err := core.CallMethod(result, "__getitem__", []interface{}{
		&api.Slice{Start: p.Offset, Stop: p.Offset + p.Limit},
	})
	if err != nil {
		return nil, err
	}
	
	return sliced, nil
}

type TimestampCursorPagination struct {
	api.BasePagination
	PageSize       int
	PageSizeParam  string
	MaxPageSize    int
	Ordering       string
	CursorParam    string
	EncodedCursor  string
	HasNext        bool
	HasPrevious    bool
}

func NewTimestampCursorPagination() *TimestampCursorPagination {
	return &TimestampCursorPagination{
		BasePagination: api.NewBasePagination(),
		PageSize:       25,
		PageSizeParam:  "page_size",
		MaxPageSize:    100,
		Ordering:       "-created_at",
		CursorParam:    "cursor",
	}
}

func (p *TimestampCursorPagination) GetPageSize(request *core.Request) int {
	if p.PageSizeParam != "" {
		sizeStr := request.GetQueryParam(p.PageSizeParam)
		if sizeStr != "" {
			size, err := strconv.Atoi(sizeStr)
			if err == nil && size > 0 {
				if p.MaxPageSize > 0 && size > p.MaxPageSize {
					return p.MaxPageSize
				}
				return size
			}
		}
	}
	return p.PageSize
}

func (p *TimestampCursorPagination) GetNextLink() string {
	if !p.HasNext {
		return ""
	}
	
	return p.BuildLink(p.GetNextCursor())
}

func (p *TimestampCursorPagination) GetPreviousLink() string {
	if !p.HasPrevious {
		return ""
	}
	
	return p.BuildLink(p.GetPreviousCursor())
}

func (p *TimestampCursorPagination) GetNextCursor() string {
	return "next_cursor_placeholder"
}

func (p *TimestampCursorPagination) GetPreviousCursor() string {
	return "previous_cursor_placeholder"
}

func (p *TimestampCursorPagination) BuildLink(cursor string) string {
	if p.Request == nil {
		return ""
	}
	
	uri, err := url.Parse(p.Request.URL)
	if err != nil {
		return ""
	}
	
	query := uri.Query()
	query.Set(p.CursorParam, cursor)
	
	if p.PageSizeParam != "" && p.GetPageSize(p.Request) != p.PageSize {
		query.Set(p.PageSizeParam, strconv.Itoa(p.GetPageSize(p.Request)))
	}
	
	uri.RawQuery = query.Encode()
	return uri.String()
}

func (p *TimestampCursorPagination) GetPaginatedResponse(data interface{}) *api.Response {
	return api.NewResponse(map[string]interface{}{
		"next":      p.GetNextLink(),
		"previous":  p.GetPreviousLink(),
		"page_size": p.GetPageSize(p.Request),
		"results":   data,
	})
}

func (p *TimestampCursorPagination) Paginate(request *core.Request, queryset interface{}) (interface{}, error) {
	p.Request = request
	pageSize := p.GetPageSize(request)
	
	p.EncodedCursor = request.GetQueryParam(p.CursorParam)
	
	
	ordered, err := core.CallPythonFunction("django.db.models", "QuerySet.order_by", []interface{}{queryset, p.Ordering})
	if err != nil {
		return nil, err
	}
	
	limited, err := core.CallMethod(ordered, "__getitem__", []interface{}{
		&api.Slice{Start: 0, Stop: pageSize + 1},
	})
	if err != nil {
		return nil, err
	}
	
	items, err := core.CallPythonFunction("builtins", "list", []interface{}{limited})
	if err != nil {
		return nil, err
	}
	
	itemsList := items.([]interface{})
	
	p.HasNext = len(itemsList) > pageSize
	p.HasPrevious = p.EncodedCursor != ""
	
	if p.HasNext {
		itemsList = itemsList[:pageSize]
	}
	
	return itemsList, nil
}

func init() {
	api.RegisterPagination("StandardResultsSetPagination", NewStandardResultsSetPagination())
	api.RegisterPagination("LargeResultsSetPagination", NewLargeResultsSetPagination())
	api.RegisterPagination("CustomLimitOffsetPagination", NewCustomLimitOffsetPagination())
	api.RegisterPagination("TimestampCursorPagination", NewTimestampCursorPagination())
}
