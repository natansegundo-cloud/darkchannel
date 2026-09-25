# Licenças e dependências locais

## Pipeline visual ativo

O compositor vetorial usa apenas a biblioteca padrão do Python e o formato aberto SVG. Personagens, objetos, fundos e cenas em `assets/` foram criados especificamente para o Capital Oculto pelo código deste projeto e podem ser usados comercialmente no canal.

As fontes declaradas no SVG são fontes de sistema por fallback. Antes da publicação, a renderização deve usar uma fonte instalada com permissão de uso comercial; o sistema funciona mesmo sem baixar fonte externa.

## Narração

A voz oficial é SANTA (`pm_santa`) no pipeline Kokoro ONNX. As versões dos pacotes e licenças instaladas estão no snapshot CSV mais recente em `docs/inventario_dependencias_*.csv`. O modelo Kokoro deve permanecer acompanhado de sua licença Apache-2.0 e o runtime `kokoro-onnx` de sua licença MIT.

## Benchmark visual desativado

O ComfyUI 0.37.0 usa GPL-3.0. Os modelos Segmind Tiny-SD e Stable Diffusion v1.5 testados usam CreativeML OpenRAIL-M, com restrições previstas nessa licença. Os binários foram removidos; fontes, revisões e hashes continuam em `config/modelos_visuais.json`.

Este registro ajuda a auditoria, mas não substitui revisão jurídica. Nenhum asset protegido, marca, rosto real ou personagem de terceiro deve ser incorporado à biblioteca sem permissão documentada.
