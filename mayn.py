import os
import json
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables de entorno
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))
GROUP_ID = int(os.environ.get('GROUP_ID'))

# Archivo de base de datos
DB_FILE = 'database.json'

# Cargar base de datos
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"users": {}, "tips": {}, "purchases": {}}

# Guardar base de datos
def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

db = load_db()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    
    # Registrar usuario si no existe
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "subscription_end": None,
            "referrals": 0,
            "created_at": datetime.now().isoformat()
        }
        save_db(db)
    
    welcome_text = f"""
🎯 **Bienvenido a NexaPicks VIP, {user.first_name}!**

Somos tipsters profesionales especializados en predicciones deportivas de fútbol y baloncesto.

**Nuestros Planes:**

⚽ **Plan Básico** - 3.99€
• Cuotas de 1.40 a 1.70
• Acceso por 7 días

🏀 **Plan Combinadas** - 7.99€
• Cuotas de 2.00 a 3.00
• Acceso por 15 días

💎 **Suscripción Mensual** - 29.99€
• Acceso completo al grupo VIP
• Todos los tips del mes
• Análisis profesional

**Comandos disponibles:**
/pagar - Ver instrucciones de pago
/estado - Ver tu estado de suscripción
/help - Ver todos los comandos

¡Únete y empieza a ganar con nosotros!
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📋 **Comandos Disponibles:**

**Para Usuarios:**
/start - Mensaje de bienvenida
/pagar - Ver instrucciones de pago
/estado - Ver tu estado de suscripción
/help - Ver esta ayuda

**Para Admin:**
/verificar [user_id] [plan] - Verificar pago de un usuario
/stats - Ver estadísticas del bot
/creartip [cuota] [precio] [descripción] - Crear nuevo tip
/tips - Ver todos los tips disponibles
/verificartip [user_id] [tip_id] - Verificar compra de tip
/enviartip [mensaje] - Enviar tip a todos los suscriptores
/bloquear [user_id] - Bloquear usuario
/desbloquear [user_id] - Desbloquear usuario
/usuarios - Listar todos los usuarios
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Comando /pagar
async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment_text = """
💳 **Métodos de Pago:**

**Bizum:**
📱 Número: 630541014

**Transferencia Bancaria:**
🏦 IBAN: ES12 1583 0001 1490 2263 5380
👤 Titular: Oriol Masgrau Bruno

**Planes Disponibles:**
• Plan Básico: 3.99€ (7 días)
• Plan Combinadas: 7.99€ (15 días)
• Suscripción Mensual: 29.99€ (30 días)

**Instrucciones:**
1. Realiza el pago por Bizum o transferencia
2. Envía una captura de pantalla del pago al admin
3. Espera la verificación (normalmente en minutos)
4. Recibirás acceso automático al grupo VIP

¡Gracias por confiar en NexaPicks!
    """
    await update.message.reply_text(payment_text, parse_mode='Markdown')

# Comando /estado
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id not in db["users"]:
        await update.message.reply_text("❌ No estás registrado. Usa /start para comenzar.")
        return
    
    user = db["users"][user_id]
    subscription_end = user.get("subscription_end")
    
    if subscription_end:
        end_date = datetime.fromisoformat(subscription_end)
        if end_date > datetime.now():
            days_left = (end_date - datetime.now()).days
            status_text = f"""
✅ **Suscripción Activa**

📅 Vence el: {end_date.strftime('%d/%m/%Y')}
⏳ Días restantes: {days_left}

¡Disfruta de tus predicciones VIP!
            """
        else:
            status_text = """
❌ **Suscripción Expirada**

Tu suscripción ha vencido. Usa /pagar para renovar y seguir accediendo a nuestros tips premium.
            """
    else:
        status_text = """
❌ **Sin Suscripción Activa**

Actualmente no tienes una suscripción activa. Usa /pagar para ver los planes disponibles y unirte al VIP.
        """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

# Comando /verificar (solo admin)
async def verificar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Este comando es solo para administradores.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /verificar [user_id] [plan]\nPlanes: basico, combinada, mensual")
        return
    
    user_id = context.args[0]
    plan = context.args[1].lower()
    
    # Determinar días según el plan
    days_map = {
        "basico": 7,
        "combinada": 15,
        "mensual": 30
    }
    
    if plan not in days_map:
        await update.message.reply_text("❌ Plan inválido. Usa: basico, combinada, mensual")
        return
    
    days = days_map[plan]
    
    # Actualizar suscripción
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "username": None,
            "first_name": None,
            "subscription_end": None,
            "referrals": 0,
            "created_at": datetime.now().isoformat()
        }
    
    # Si ya tiene suscripción activa, extender desde la fecha de vencimiento
    current_end = db["users"][user_id].get("subscription_end")
    if current_end:
        current_end_date = datetime.fromisoformat(current_end)
        if current_end_date > datetime.now():
            new_end = current_end_date + timedelta(days=days)
        else:
            new_end = datetime.now() + timedelta(days=days)
    else:
        new_end = datetime.now() + timedelta(days=days)
    
    db["users"][user_id]["subscription_end"] = new_end.isoformat()
    save_db(db)
    
    # Generar enlace de invitación
    try:
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1,
            expire_date=datetime.now() + timedelta(hours=24)
        )
        
        # Enviar enlace al usuario
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"""
✅ **¡Pago Verificado!**

Tu suscripción ha sido activada con éxito.

📅 Válida hasta: {new_end.strftime('%d/%m/%Y')}
🔗 Enlace al grupo VIP: {invite_link.invite_link}

⚠️ Este enlace expira en 24 horas y solo puede usarse una vez.

¡Bienvenido a NexaPicks VIP!
            """,
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(f"✅ Usuario {user_id} verificado. Plan: {plan} ({days} días)")
        
    except Exception as e:
        logger.error(f"Error al crear enlace de invitación: {e}")
        await update.message.reply_text(f"❌ Error al generar enlace: {e}")

# Comando /stats (solo admin)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Este comando es solo para administradores.")
        return
    
    total_users = len(db["users"])
    active_subs = sum(1 for u in db["users"].values() 
                     if u.get("subscription_end") and 
                     datetime.fromisoformat(u["subscription_end"]) > datetime.now())
    
    total_tips = len(db.get("tips", {}))
    total_purchases = len(db.get("purchases", {}))
    
    # Calcular ingresos aproximados
    basic_count = sum(1 for u in db["users"].values() 
                     if u.get("last_plan") == "basico")
    combined_count = sum(1 for u in db["users"].values() 
                        if u.get("last_plan") == "combinada")
    monthly_count = sum(1 for u in db["users"].values() 
                       if u.get("last_plan") == "mensual")
    
    total_revenue = (basic_count * 3.99) + (combined_count * 7.99) + (monthly_count * 29.99)
    
    stats_text = f"""
📊 **Estadísticas del Bot**

👥 **Usuarios:**
• Total: {total_users}
• Suscriptores activos: {active_subs}

💰 **Ingresos Estimados:**
• Plan Básico: {basic_count} x 3.99€ = {basic_count * 3.99:.2f}€
• Plan Combinadas: {combined_count} x 7.99€ = {combined_count * 7.99:.2f}€
• Suscripción Mensual: {monthly_count} x 29.99€ = {monthly_count * 29.99:.2f}€
• **Total: {total_revenue:.2f}€**

🎯 **Tips:**
• Total creados: {total_tips}
• Total compras: {total_purchases}
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# Comando /creartip (solo admin)
async def creartip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Este comando es solo para administradores.")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("❌ Uso: /creartip [cuota] [precio] [descripción]")
        return
    
    cuota = context.args[0]
    precio = context.args[1]
    descripcion = " ".join(context.args[2:])
    
    tip_id = f"tip_{int(datetime.now().timestamp())}"
    
    if "tips" not in db:
        db["tips"] = {}
    
    db["tips"][tip_id] = {
        "cuota": cuota,
        "precio": precio,
        "descripcion": descripcion,
        "created_at": datetime.now().isoformat()
    }
    save_db(db)
    
    await update.message.reply_text(f"✅ Tip creado con ID: {tip_id}")

# Comando /tips
async def tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "tips" not in db or not db["tips"]:
        await update.message.reply_text("❌ No hay tips disponibles actualmente.")
        return
    
    tips_text = "🎯 **Tips Disponibles:**\n\n"
    
    for tip_id, tip in db["tips"].items():
        tips_text += f"**Cuota:** {tip['cuota']} | **Precio:** {tip['precio']}€\n"
        tips_text += f"📝 {tip['descripcion']}\n"
        tips_text += f"🆔 Usa: /comprartip {tip_id}\n\n"
    
    await update.message.reply_text(tips_text, parse_mode='Markdown')

# Comando /comprartip
async def comprartip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("❌ Uso: /comprartip [tip_id]")
        return
    
    tip_id = context.args[0]
    user_id = str(update.effective_user.id)
    
    if "tips" not in db or tip_id not in db["tips"]:
        await update.message.reply_text("❌ Tip no encontrado.")
        return
    
    # Verificar si ya compró este tip
    if "purchases" not in db:
        db["purchases"] = {}
    
    purchase_key = f"{user_id}_{tip_id}"
    if purchase_key in db["purchases"]:
        await update.message.reply_text("❌ Ya has comprado este tip.")
        return
    
    tip = db["tips"][tip_id]
    
    payment_text = f"""
💳 **Comprar Tip**

**Cuota:** {tip['cuota']}
**Precio:** {tip['precio']}€

**Métodos de Pago:**

**Bizum:**
📱 Número: 630541014

**Transferencia Bancaria:**
🏦 IBAN: ES12 1583 0001 1490 2263 5380
👤 Titular: Oriol Masgrau Bruno

**Instrucciones:**
1. Realiza el pago de {tip['precio']}€
2. Envía una captura de pantalla del pago al admin
3. Menciona el ID del tip: {tip_id}
4. Recibirás el tip una vez verificado el pago
    """
    
    await update.message.reply_text(payment_text, parse_mode='Markdown')

# Comando /verificartip (solo admin)
async def verificartip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Este comando es solo para administradores.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /verificartip [user_id] [tip_id]")
        return
    
    user_id = context.args[0]
    tip_id = context.args[1]
    
    if "tips" not in db or tip_id not in db["tips"]:
        await update.message.reply_text("❌ Tip no encontrado.")
        return
    
    tip = db["tips"][tip_id]
    purchase_key = f"{user_id}_{tip_id}"
    
    if "purchases" not in db:
        db["purchases"] = {}
    
    db["purchases"][purchase_key] = {
        "user_id": user_id,
        "tip_id": tip_id,
        "purchased_at": datetime.now().isoformat()
    }
    save_db(db)
    
    # Enviar tip al usuario
    await context.bot.send_message(
        chat_id=int(user_id),
        text=f"""
✅ **¡Pago Verificado!**

Aquí está tu tip:

**Cuota:** {tip['cuota']}
📝 **Detalles:** {tip['descripcion']}

¡Buena suerte!
        """,
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(f"✅ Tip {tip_id} entregado al usuario {user_id}")

# Comando /enviartip (solo admin)
async def enviartip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Este comando es solo para administradores.")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("❌ Uso: /enviartip [mensaje]")
        return
    
    mensaje = " ".join(context.args)
    
    # Enviar a todos los suscriptores activos
    sent_count = 0
    for user_id, user in db["users"].items():
        subscription_end = user.get("subscription_end")
        if subscription_end:
            end_date = datetime.fromisoformat(subscription_end)
            if end_date > datetime.now():
                try:
                    await context.bot.send_message(
                        chat_id=int(user_id),
                        text=f"🎯 **Nuevo Tip de NexaPicks**\n\n{mensaje}",
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error enviando a {user_id}: {e}")
    
    await update.message.reply_text(f"✅ Tip enviado a {sent_count} suscriptores activos")

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("pagar", pagar))
    application.add_handler(CommandHandler("estado", estado))
    application.add_handler(CommandHandler("verificar", verificar))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("creartip", creartip))
    application.add_handler(CommandHandler("tips", tips))
    application.add_handler(CommandHandler("comprartip", comprartip))
    application.add_handler(CommandHandler("verificartip", verificartip))
    application.add_handler(CommandHandler("enviartip", enviartip))
    
    # Iniciar bot
    logger.info("Bot iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
