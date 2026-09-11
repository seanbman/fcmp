/** @type {import('ts-jest').JestConfigWithTsJest} **/
module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  setupFilesAfterEnv: ["<rootDir>/tests/setup.ts"],
  transform: {
    "^.+.ts?$": ["ts-jest", {}],
  },
  moduleNameMapper: {
    "^\\.\\./socket$": "<rootDir>/socket.ts",
    "^\\.\\./api$": "<rootDir>/api.ts",
    "^\\.\\./hooks$": "<rootDir>/hooks.ts",
    "^\\.\\./neith_types$": "<rootDir>/neith_types.ts",
  },
};
