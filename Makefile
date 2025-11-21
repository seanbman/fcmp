.PHONY: templ example

make:
	go run .

test:
	go test ./... -v
	cd static/assets && npm install && npm test
coverage:
	go test ./... -v -coverprofile=cover.out
	go tool cover -html=coverage.out

assets: templ
	tsc -p "static/assets/"
	./es-build
	./tailwindcss -i static/assets/stylesheets/tailwind.css -o static/assets/stylesheets/tailwind.min.css --minify
	sass static/assets/sass:static/assets/stylesheets

bundle:
	./esbuild static/assets/index.ts --bundle --minify --outfile=static/assets/fncmp.min.js

templ:
	/Users/seanburman/go/bin/templ generate

tsc:
	tsc -p "static/assets/" --watch

tailwind:
	./tailwindcss -i static/assets/stylesheets/tailwind.css -o static/assets/stylesheets/tailwind.min.css --watch --minify

sass:
	sass --watch static/assets/sass:static/assets/stylesheets

publish:
	git tag -s v0.3.305 -m "fncmp v0.3.305" && \
	git push --tags && \
	GOPROXY=proxy.golang.org go list -m github.com/snburman/fncmp@v0.3.305 && \
	curl https://sum.golang.org/lookup/github.com/snburman/fncmp@v0.3.305