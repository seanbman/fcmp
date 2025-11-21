/** @type {import('ts-jest').JestConfigWithTsJest} **/
module.exports = {
preset: "ts-jest",
  testEnvironment: "node",
  transform: {
    "^.+.ts?$": ["ts-jest",{}],
  },
  moduleNameMapper: {
    "../socket": "../socket.ts",
    "./api": "./api.ts",
    "../fncmp_types": "../fncmp_types.ts",
    "./fncmp_types": "./fncmp_types.ts",
  }
};