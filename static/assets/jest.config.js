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
    "../fcmp_types": "../fcmp_types.ts",
    "./fcmp_types": "./fcmp_types.ts",
  }
};