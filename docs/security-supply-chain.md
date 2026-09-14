# Segurança da cadeia de dependências (#27)

O BriskMail usa os controles nativos do GitHub para evitar que dependências
vulneráveis sejam introduzidas e para encontrar padrões de segurança no código.
Eles complementam, mas não substituem, o `ci-gate`: o gate continua presente em
todo PR e push para `main`, sem filtros de caminho.

## Controles

- Dependabot verifica semanalmente `pip` e `github-actions`. Atualizações de
  correção e menores são agrupadas, com no máximo três PRs abertos por ecossistema.
  Atualizações de segurança continuam tratadas como PRs explícitos do GitHub.
- Dependency review roda em todos os PRs para `main`. Ele falha quando uma
  mudança introduz uma dependência com vulnerabilidade de severidade alta ou
  crítica; não precisa de permissões para comentar no PR.
- CodeQL analisa Python e JavaScript/TypeScript em PRs, pushes para `main` e
  semanalmente. O upload de resultados requer somente `security-events: write`;
  o restante do workflow permanece somente-leitura.

## Triagem de alertas

O responsável operacional é Bruno Teixeira Lopes. Revise alertas novos no dia
útil seguinte e registre uma das decisões: corrigir, aceitar temporariamente
com prazo de revisão, ou descartar com justificativa verificável. Priorize
vulnerabilidades exploráveis no runtime de produção, depois dependências de
desenvolvimento e alertas de qualidade do CodeQL.

Não silencie uma falha do dependency review, um alerta do Dependabot ou um
achado do CodeQL apenas para obter um check verde. Quando a correção exigir
mudança funcional, atualização ampla ou decisão de arquitetura, abra uma issue
separada com o alerta, impacto, versão afetada e plano de validação.

## Atualizações do Dependabot

PRs de correção e menores agrupados ainda precisam do `ci-gate` e da revisão
normal. Atualizações maiores são avaliadas individualmente: leia notas de
release, execute a suíte aplicável e não misture mudanças de comportamento no
PR automático. Dependabot mantém os SHAs de actions atualizados; nunca troque
um SHA por tag, branch ou `@master`.

## Falsos positivos e exceções

Antes de descartar um alerta, confirme que a dependência, versão e caminho de
execução não afetam o projeto. Registre o motivo, fonte e data de reavaliação
na issue ou no alerta do GitHub. Exceções são temporárias, têm responsável e
não substituem a correção quando ela se tornar viável.

## Separação futura de dependências

`requirements.txt` contém atualmente dependências de runtime e de teste. Esta
issue não introduz lockfile, hashes ou separação de arquivos, pois isso altera
a estratégia de empacotamento do container. Uma issue futura deve avaliar
`requirements-runtime.txt` e `requirements-dev.txt`, preservando builds e CI
reprodutíveis antes de migrar.

## Ativação e primeira revisão

`dependabot.yml`, dependency review e CodeQL são versionados e validados no PR.
Dependabot alerts e Dependabot security updates são configurações remotas do
repositório: devem ser habilitados somente após aprovação explícita do owner.
Depois da primeira execução do CodeQL e da habilitação dos alertas, revise os
achados e converta problemas relevantes em issues separadas; não altere todas
as dependências no mesmo PR.

### Registro inicial — 2026-09-10

Com aprovação do owner, Dependency graph, Dependabot alerts e Dependabot
security updates foram habilitados. A primeira execução do CodeQL para Python e
JavaScript/TypeScript não encontrou alertas abertos. A primeira triagem do
Dependabot encontrou 11 alertas: oito para `python-multipart`, um para
`python-dotenv`, um para `pytest` e um para `PyPDF2`. Eles foram separados em
[#40](https://github.com/Brunotlps/email-classifier/issues/40),
[#37](https://github.com/Brunotlps/email-classifier/issues/37),
[#39](https://github.com/Brunotlps/email-classifier/issues/39) e
[#38](https://github.com/Brunotlps/email-classifier/issues/38), respectivamente.
Nenhuma dependência foi atualizada como parte da infraestrutura de segurança.

### Correção do alerta do PyPDF2 — issue #38

O parser PDF foi migrado de `PyPDF2` para `pypdf==6.18.1`, com cobertura para
extração de texto e para o erro de instalação ausente. Após a integração,
confirme que o alerta Dependabot `GHSA-4vvm-4w3v-6mr8` foi encerrado; até essa
confirmação, ele permanece aberto no GitHub.

Referências: [Dependabot](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart),
[dependency review](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review),
[CodeQL](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning).
