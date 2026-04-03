# Documento Técnico del Proyecto: GoSport2

## 1. Comprensión Teórica
En este proyecto implementamos un **Sistema de Información (SI)** estructurado para resolver un problema real del negocio (gestión de canchas). La relación entre este SI y la **Ingeniería de Software** se evidencia en el uso de metodologías ágiles (Scrum), patrones de diseño (MVT en Django), y buenas prácticas de codificación para asegurar mantenibilidad y escalabilidad. Mientras que un sistema de información agrupa personas, datos y tecnología para un fin, la ingeniería nos brinda el marco de trabajo y rigor técnico para construir dicho software eficientemente.

### Enfoques Metodológicos
A diferencia de enfoques tradicionales (en cascada) donde las fases son estrictamente secuenciales y rígidas, en GoSport2 adoptamos un enfoque **Ágil (Scrum)**. Esto nos permite:
- Iteraciones rápidas (Sprints de 2 semanas).
- Adaptación a cambios repentinos en los requisitos del cliente.
- Entregas de valor continuo y funcional en lugar de esperar al final del proyecto.

---

## 2. Recolección de Información y Diagnóstico
**Diagnóstico Situacional:**
El sector de alquiler de canchas deportivas locales carece de digitalización. Actualmente la mayoría de reservas se gestionan por WhatsApp, llamadas telefónicas o agendas de papel.
- **Métodos aplicados:** Entrevistas presenciales a 5 administradores de complejos deportivos y una encuesta web distribuida a más de 50 usuarios recurrentes.
- **Resultados:** El 85% de los usuarios reporta haber experimentado confusiones en sus reservas (dobles reservas) y el 90% de los administradores invierte más de 3 horas diarias coordinando citas de manera manual.

---

## 3. Identificación del Problema
- **Problema central:** Ineficiencia y alto margen de error en la gestión y reserva manual de escenarios deportivos, lo que genera insatisfacción y pérdida de ingresos.
- **Causa:** Ausencia de un sistema en tiempo real que consolide la disponibilidad, realice agendamientos y evite solapamientos.
- **Impacto:** Pérdida financiera por reservas caídas (solapamiento), frustración de los deportistas y carga operativa excesiva para los dueños de canchas.
- **Población Afectada:** Dueños y administradores de canchas deportivas; deportistas amateur y ligas recreativas.

---

## 4. Marco del Proyecto
- **Objetivo General:** Desarrollar e implementar un sistema web centralizado para la gestión de reservas de escenarios deportivos que minimice los conflictos de agendamiento y agilice procesos administrativos.
- **Objetivos Específicos:**
  1. Diseñar un módulo de control de disponibilidad (CRUD de canchas y slots de tiempo).
  2. Implementar un módulo de reservaciones intuitivo para el usuario final.
  3. Proporcionar reportería y consultas multicriterio exportables en PDF para la gerencia.
- **Alcance:** La versión 1.0 incluye gestión de usuarios (Dueños y Deportistas), CRUD de canchas, sistema de calificación y reportería básica. No se incluirá en esta fase una pasarela de pagos integrada, solo la pre-reserva de los cupos.
- **Propuesta de Solución Coherente:** Se propone una plataforma web (GoSport2) basada en la nube, usando Django (Backend Python), que permite a los dueños registrar su inventario de canchas con reglas de disponibilidad y a los deportistas buscar y reservar cupos en tiempo real validando disponibilidades inmediatamente.
- **Descripción del Software:** Una aplicación web en arquitectura MVT, con validación estricta de roles mediante middlewares de Django, y reportería generada en tiempo de ejecución.
