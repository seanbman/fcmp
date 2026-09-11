package neith

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"net/http"
)

var errSessionNotFound = errors.New("neith session not found")

func newSessionID() (string, error) {
	buf := make([]byte, 32)
	if _, err := rand.Read(buf); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(buf), nil
}

func (r *runtime) sessionID(req *http.Request) (string, error) {
	if r == nil || req == nil {
		return "", errSessionNotFound
	}
	cookie, err := req.Cookie(r.Config().SessionCookieName)
	if err != nil || cookie.Value == "" {
		return "", errSessionNotFound
	}
	return cookie.Value, nil
}

func (r *runtime) ensureSessionID(w http.ResponseWriter, req *http.Request) (string, error) {
	if id, err := r.sessionID(req); err == nil {
		return id, nil
	}

	id, err := newSessionID()
	if err != nil {
		return "", err
	}
	secure := r.Config().SessionCookieSecure
	if req != nil && req.TLS != nil {
		secure = true
	}
	http.SetCookie(w, &http.Cookie{
		Name:     r.Config().SessionCookieName,
		Value:    id,
		Path:     r.Config().SessionCookiePath,
		HttpOnly: true,
		Secure:   secure,
		SameSite: http.SameSiteLaxMode,
	})
	return id, nil
}
