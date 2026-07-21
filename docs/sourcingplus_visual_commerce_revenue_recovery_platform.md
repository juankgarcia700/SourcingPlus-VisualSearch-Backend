# SourcingPlus Visual Commerce & Revenue Recovery Platform

**Documento maestro del modelo de producto, valor y monetización**  
**Estado:** Propuesta formal para aprobación  
**Versión:** 1.0  
**Fecha:** 20 de julio de 2026

---

## 1. Declaración estratégica

SourcingPlus es una plataforma de inteligencia aplicada al comercio que convierte imágenes, texto, documentos y otras expresiones de intención de compra en productos identificados y pedidos correctos, procesables y medibles.

La plataforma integra descubrimiento visual, captura inteligente, prevención de errores y recuperación de pedidos bajo dos promesas de valor complementarias:

> **Encuentra lo que el cliente quiere comprar.**

> **Evita que el pedido falle y recupera el que la operación no pudo procesar.**

SourcingPlus no se concibe como un buscador aislado ni como un servicio intensivo de consultoría. Su objetivo es convertirse en un producto SaaS de baja intervención operativa, con conectores estandarizados, medición automática y monetización ligada al resultado económico demostrado.

---

## 2. Propósito

SourcingPlus busca resolver tres pérdidas recurrentes en los canales digitales, venta directa y venta por catálogo:

1. **Demanda que no encuentra el producto:** el comprador tiene una imagen o una necesidad, pero no conoce la referencia o las palabras correctas para buscarla.
2. **Pedidos que nacen con errores:** códigos mal digitados, campañas equivocadas, variantes inválidas, información incompleta o selección incorrecta.
3. **Pedidos que se pierden en la operación:** órdenes rechazadas, detenidas, enviadas a cola o abandonadas antes de la confirmación.

El resultado esperado es mejorar la conversión, elevar el procesamiento correcto en el primer intento, reducir el reproceso y proteger ingresos que de otra manera se perderían.

---

## 3. Posicionamiento

### Categoría de producto

**Visual Commerce, Intelligent Order Capture & Revenue Recovery Platform.**

### Propuesta de valor

SourcingPlus permite a comercios, retailers y compañías de venta directa:

- encontrar productos mediante imágenes y lenguaje natural;
- transformar entradas no estructuradas en borradores de pedido;
- validar productos, variantes y condiciones antes del envío;
- corregir excepciones y recuperar pedidos en riesgo;
- medir el valor económico atribuido, protegido y rescatado;
- pagar principalmente por resultados verificables.

### Diferenciación

SourcingPlus no cobra únicamente por disponer de una funcionalidad. El modelo comercial se alinea con el cliente mediante success fees calculados sobre ventas netas atribuibles a la intervención de la plataforma.

---

## 4. Mercado y verticales

El núcleo tecnológico será horizontal. Las reglas de relevancia, atributos y validaciones se configurarán mediante Vertical Packs.

| Vertical | Necesidades principales |
|---|---|
| Moda y prendas | Estilo, silueta, color, patrón, material, talla y variante |
| Venta directa y por catálogo | Campaña, catálogo, referencia, asesora, talla, color y disponibilidad |
| Retail general | Categoría, marca, precio, disponibilidad y productos equivalentes |
| Ferretería y mejoramiento del hogar | Uso, medida, material, potencia, voltaje y especificación técnica |
| Repuestos de autos y motos | OEM, MPN, vehículo, modelo, año, posición y compatibilidad |

En repuestos y categorías técnicas, la similitud visual identifica candidatos, pero no sustituye la validación de compatibilidad.

---

## 5. Portafolio funcional

### 5.1 Visual Discovery

Ayuda al cliente a encontrar productos utilizando:

- fotografía o captura de pantalla;
- URL de imagen;
- texto descriptivo;
- combinación de imagen y texto;
- filtros de negocio;
- productos visualmente relacionados.

El módulo debe llevar al usuario al producto o variante correcta y registrar la contribución de la búsqueda a la conversión.

### 5.2 Intelligent Order Capture

Convierte entradas no estructuradas en líneas de pedido mediante:

- OCR;
- reconocimiento visual;
- fuzzy matching de referencias;
- interpretación de texto;
- lectura de PDF o páginas de catálogo;
- captura desde mensajes o listas;
- generación de un borrador estructurado;
- asignación de un nivel de confianza.

### 5.3 Order Assurance

Previene errores antes de enviar el pedido:

- referencia inexistente;
- producto de otra campaña;
- talla o color inválido;
- variante descontinuada;
- producto sin disponibilidad;
- cantidad atípica;
- duplicidad;
- información incompleta;
- incompatibilidad técnica.

Los casos de confianza alta pueden automatizarse. Los casos ambiguos requieren confirmación humana.

### 5.4 Revenue Recovery

Gestiona pedidos ya rechazados, detenidos o enviados a cola:

- identifica la causa;
- encuentra candidatos de corrección;
- propone sustitutos autorizados;
- solicita aprobación cuando corresponde;
- reenvía el pedido corregido;
- registra el valor recuperado;
- controla cancelaciones y devoluciones posteriores.

### 5.5 Commerce Intelligence

Entrega analítica operativa y financiera:

- búsquedas y productos encontrados;
- tasa de búsquedas sin resultado;
- errores de captura;
- First-Pass Order Acceptance;
- Straight-Through Processing;
- pedidos en cola;
- GMV atribuido, protegido y rescatado;
- precisión y confianza del modelo;
- causas recurrentes;
- valor facturable de SourcingPlus.

---

## 6. Flujo integral

1. El comprador o vendedor expresa una intención mediante imagen, texto, documento o captura manual.
2. SourcingPlus identifica productos y variantes candidatas.
3. El motor valida catálogo, campaña, precio, inventario y reglas aplicables.
4. Si la confianza es alta, genera o completa el pedido.
5. Si existe ambigüedad, solicita confirmación.
6. Si el pedido ya falló, activa Revenue Recovery.
7. La plataforma registra cada intervención en el ledger de atribución.
8. La venta facturada y no devuelta determina el resultado económico y el success fee.

---

## 7. Principios del modelo comercial

### 7.1 Pay for Performance

El modelo principal no se basará en planes tradicionales por funcionalidad. La facturación se vinculará al resultado económico:

\[
\text{Fee mensual}=
\alpha(\text{GMV visual atribuido})+
\beta(\text{GMV protegido})+
\gamma(\text{GMV rescatado})
\]

### 7.2 Rangos iniciales para validación

| Resultado | Base de cálculo | Rango inicial |
|---|---|---:|
| Visual Commerce | GMV neto directamente atribuido | 0,50%–1,00% |
| Order Assurance | GMV neto protegido | 0,50%–1,00% |
| Revenue Recovery | GMV neto rescatado | 1,50%–3,00% |

Los porcentajes son hipótesis comerciales. Deben validarse por industria, margen, ticket, complejidad y calidad de atribución.

### 7.3 Mínimo operativo acreditable

Para cubrir infraestructura en periodos de bajo volumen podrá aplicarse:

\[
\text{Factura}=\max(\text{mínimo operativo},\text{success fee})
\]

El mínimo operativo no se suma al success fee. Queda completamente acreditado dentro del valor calculado por desempeño.

Durante pilotos iniciales podrá eliminarse temporalmente para reducir la barrera de entrada.

### 7.4 Baja dependencia de consultoría

La mezcla de ingresos objetivo será:

| Fuente | Participación objetivo |
|---|---:|
| Success fees y consumo transaccional | 80%–90% |
| Implementación estandarizada | 5%–10% |
| Consultoría y personalización | Máximo 5%–10% |

El producto debe diseñarse para operar con mínima intervención del fundador mediante onboarding guiado, conectores estándar, medición automática, documentación y soporte escalable.

---

## 8. Definiciones económicas

### GMV visual atribuido

Venta neta de productos identificados o seleccionados directamente desde una interacción de SourcingPlus y comprados dentro de la ventana de atribución acordada.

### GMV protegido

Venta neta de un pedido con un error técnicamente demostrable que SourcingPlus corrigió antes del rechazo y que posteriormente fue aceptado y facturado.

### GMV rescatado

Venta neta de un pedido previamente rechazado, detenido o enviado a cola, corregido mediante SourcingPlus y posteriormente facturado.

### GMV influenciado

Venta en la que SourcingPlus participó, pero cuya incrementalidad no puede demostrarse completamente. Debe informarse, pero no necesariamente facturarse.

### GMV incremental

Venta adicional estimada mediante un grupo de control, experimento A/B o metodología estadística acordada.

### Base facturable

La base recomendada es la venta neta facturada, excluyendo:

- IVA e impuestos indirectos;
- transporte;
- cancelaciones;
- devoluciones;
- fraude;
- duplicados;
- recuperaciones manuales no atribuibles;
- productos ajenos a la intervención;
- transacciones fuera de la ventana acordada.

---

## 9. Revenue Attribution Ledger

La atribución es una capacidad central del producto. Cada intervención deberá registrar:

- `tenant_id`;
- `store_id`;
- `campaign_id` cuando corresponda;
- `advisor_id` cuando corresponda;
- `session_id`;
- `search_id`;
- `original_order_id`;
- entrada original;
- referencia original;
- producto y variante sugeridos;
- confianza;
- corrección aceptada;
- pedido final;
- factura;
- valor neto;
- cancelación o devolución;
- regla de atribución;
- porcentaje aplicable;
- fee generado;
- evidencia auditable.

El cliente debe poder conciliar cada valor facturado. El ledger deberá ser inmutable, trazable y exportable.

---

## 10. KPI oficiales

### Visual Commerce

- Precision@1, Precision@5 y Recall@10.
- Tasa de búsquedas sin resultado.
- Click-through rate.
- Add-to-cart asistido.
- Conversión asistida.
- GMV visual atribuido.
- Latencia p50, p95 y p99.

### Captura y aseguramiento

\[
\text{First-Pass Order Acceptance}=
\frac{\text{pedidos aceptados sin corrección posterior}}
{\text{pedidos enviados}}
\]

\[
\text{Straight-Through Processing}=
\frac{\text{pedidos procesados sin intervención humana}}
{\text{pedidos recibidos}}
\]

\[
\text{Order Leakage}=
\frac{\text{pedidos iniciados no confirmados}}
{\text{pedidos iniciados}}
\]

También se medirán:

- errores prevenidos;
- pedidos en cola;
- tiempo de confirmación;
- tasa de rescate;
- falsos rescates;
- intervención manual;
- cancelaciones y devoluciones;
- GMV protegido y rescatado.

### Plataforma y negocio

- disponibilidad;
- costo por 1.000 búsquedas;
- costo por pedido analizado;
- margen de contribución;
- ingreso por cliente;
- tiempo de onboarding;
- retención;
- horas mensuales de soporte por cliente.

---

## 11. Arquitectura comercial y tecnológica

La plataforma se estructurará en cuatro capas:

1. **Motor común:** búsqueda visual, texto, ranking, OCR, validación y analítica.
2. **Plataforma SaaS:** tenants, seguridad, consumo, ledger, facturación y SLA.
3. **Conectores:** Shopify, VTEX, WooCommerce y Adobe Commerce/Magento.
4. **Vertical Packs:** configuraciones, taxonomías y evaluaciones por industria.

Los conectores no deben incorporar lógica de negocio específica dentro del motor. Cada plataforma traducirá sus datos al modelo canónico de SourcingPlus.

---

## 12. Evolución desde el repositorio actual

El proyecto parte de la Fase 8 existente y reutiliza:

- backend FastAPI;
- procesamiento de imágenes;
- embeddings CLIP;
- Pinecone;
- búsqueda por imagen, URL y texto;
- filtros de metadatos;
- SQLAlchemy;
- caché;
- telemetría;
- frontend y dashboard;
- pruebas iniciales.

La evolución será progresiva:

| Componente actual | Decisión |
|---|---|
| FastAPI y servicios modulares | Conservar y fortalecer |
| CLIP y Pinecone | Conservar como baseline y evaluar mejoras |
| SQLAlchemy | Conservar |
| SQLite | Migrar a PostgreSQL |
| Caché local | Migrar progresivamente a Redis |
| BackgroundTasks | Evolucionar a cola distribuida |
| Frontend actual | Reutilizar para demo y pilotos |
| Analítica actual | Ampliar hacia conversión, pedidos y atribución |
| Tests con mocks | Conservar y complementar con pruebas reales |

---

## 13. Roadmap optimizado

El escenario recomendado es de 15 meses, con contingencia hasta el mes 18.

| Periodo | Entrega | Resultado monetizable |
|---|---|---|
| Semanas 1–2 | Commercial Demo Ready | Demostración y piloto |
| Semanas 3–6 | Pilot Core y Shopify Skeleton | Primer piloto pagado |
| Semanas 7–10 | Shopify Beta y Smart Capture MVP | Fee por resultados iniciales |
| Semanas 11–14 | Shopify comercial | GMV visual atribuido |
| Meses 4–5 | Order Assurance & Recovery | GMV protegido y rescatado |
| Meses 5–7 | Multitenencia y VTEX MVP | Integración Business |
| Meses 7–9 | VTEX comercial | Success fees de mayor volumen |
| Meses 8–10 | Vertical Packs esenciales | Mayor precisión y adopción |
| Meses 9–11 | WooCommerce opcional | Cobertura adicional |
| Meses 9–12 | Enterprise Readiness | Discovery enterprise |
| Meses 11–14 | Adobe/Magento MVP | Contrato enterprise |
| Mes 15 | Escalamiento | Operación regional |
| Meses 16–18 | Contingencia | Cierre de brechas |

### Ruta crítica

Core → Shopify → Multitenencia → VTEX → Enterprise Readiness → Adobe/Magento.

### Ruta paralela

Smart Capture → Order Assurance → Revenue Recovery.

WooCommerce y Vertical Packs avanzados no deben retrasar la ruta crítica.

---

## 14. Principios de producto y operación

1. Monetizar desde los primeros pilotos.
2. Priorizar ingresos recurrentes sobre consultoría.
3. Construir una sola plataforma configurable.
4. No automatizar decisiones ambiguas sin confirmación.
5. Medir atribución antes de cobrar por resultados.
6. No recalcular embeddings ante cambios únicamente comerciales.
7. Mantener separados datos, reglas y consumo de cada tenant.
8. Automatizar onboarding, monitoreo y conciliación.
9. Incorporar seguridad, pruebas y documentación en cada release.
10. No avanzar por desarrollo terminado, sino por valor validado.

---

## 15. Gobierno y criterios de decisión

Cada release deberá superar cuatro validaciones:

### Técnica

- pruebas aprobadas;
- seguridad validada;
- desempeño medido;
- errores observables;
- rollback disponible.

### Producto

- problema de usuario comprobado;
- experiencia entendible;
- umbral de confianza definido;
- intervención humana correctamente ubicada.

### Económica

- evento facturable definido;
- atribución auditable;
- costo unitario conocido;
- margen de contribución positivo o ruta aprobada.

### Operativa

- onboarding repetible;
- soporte documentado;
- horas de intervención controladas;
- monitoreo automatizado.

---

## 16. Riesgos principales

| Riesgo | Control requerido |
|---|---|
| Atribución disputada | Ledger auditable y reglas contractuales |
| Falso positivo | Umbrales de confianza y confirmación humana |
| Datos de cliente mezclados | Multitenencia y namespaces |
| Dependencia de consultoría | Conectores y onboarding estandarizados |
| Costos de IA crecientes | Caché, procesamiento diferencial y límites |
| Cambios de plataformas | Versionamiento y pruebas de conectores |
| Devoluciones posteriores | Ventana de maduración antes de facturar |
| Baja precisión por industria | Vertical Packs y conjuntos de evaluación |
| Automatización prematura | Shadow mode y despliegue gradual |

---

## 17. Decisiones formalizadas

1. El nombre estratégico del producto es **SourcingPlus Visual Commerce & Revenue Recovery Platform**.
2. Las promesas son encontrar la intención de compra y evitar o recuperar la pérdida del pedido.
3. El producto será multiindustria.
4. Shopify será el primer conector comercial.
5. VTEX será el siguiente conector prioritario para Latinoamérica.
6. WooCommerce no bloqueará la ruta enterprise.
7. Adobe Commerce/Magento será la evolución enterprise.
8. El modelo comercial principal será Pay for Performance.
9. La base facturable será venta neta atribuible, protegida o rescatada.
10. La atribución será una capacidad central del producto.
11. La consultoría tendrá una participación minoritaria.
12. El proyecto evolucionará sobre la base existente del repositorio.
13. El roadmap recomendado será de 15 meses con contingencia hasta 18.
14. Ninguna automatización financiera o transaccional de baja confianza operará sin confirmación.

---

## 18. Próxima formalización requerida

Después de aprobar este documento deberán generarse, en este orden:

1. Product Requirements Document de la primera release comercial.
2. Especificación del Revenue Attribution Ledger.
3. Contrato canónico de productos, variantes, eventos y pedidos.
4. Diseño del Shopify Commercial MVP.
5. Plan de evaluación con catálogo y pedidos reales.
6. Política contractual de atribución y success fees.
7. Backlog técnico priorizado por monetización.

---

## 19. Declaración final

> **SourcingPlus no cobra por instalar un buscador. Cobra por encontrar ventas, evitar que se pierdan y recuperar las que ya estaban en riesgo.**

El éxito del producto dependerá de demostrar tres resultados de forma repetible: mejor descubrimiento, mayor aceptación de pedidos en el primer intento y recuperación económica auditable.
