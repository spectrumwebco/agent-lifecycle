package workspace

import (
	"testing"
)

// TestToID takes in a string which represents a workspace source and returns an appropriate
// _human readable_ ID for it.
// Note that these tests document the status quo and not the ideal state.
// I've created follow up tickets to adjust the ToID function and update the tests but because
// this is a potentially breaking change we'll have to wait for the next major version.
func TestToID(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{
			name:  "Simple URL, no @, parse repo name",
			input: "github.com/loft-sh/kled",
			want:  "kled",
		},
		{
			name:  "URL with .git suffix",
			input: "github.com/loft-sh/kled.git",
			want:  "kled",
		},
		{
			name:  "URL with .git suffix and https prefix",
			input: "https://github.com/loft-sh/kled.git",
			want:  "kled",
		},
		{
			name:  "URL with trailing slash",
			input: "github.com/loft-sh/devpod/",
			want:  "kled",
		},
		{
			name:  "Bare string with no slash",
			input: "myrepo",
			want:  "myrepo",
		},
		{
			name:  "Local directory",
			input: "/home/loft/kled",
			want:  "kled",
		},
		{
			name:  "Branch with valid characters",
			input: "github.com/loft-sh/kled@feature1",
			want:  "github-com-loft-sh-kled",
		},
		{
			name:  "Branch with valid characters and /",
			input: "github.com/loft-sh/kled@feat/feature1",
			want:  "feat-feature1",
		},
		{
			name:  "PR reference",
			input: "github.com/loft-sh/kled@pr/123",
			want:  "pr-123",
		},
		{
			name:  "Truncation beyond 48 characters",
			input: "github.com/loft-sh/kledreallylongreponame_that_exceeds_48_characters_total_length",
			want:  "kledreallylongreponamethatexceeds48characterst",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ToID(tt.input)
			if got != tt.want {
				t.Errorf("ToID(%q) = %q, want %q", tt.input, got, tt.want)
			}
		})
	}
}
