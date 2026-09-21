const logger = require('./loggerService');

function charge(cardNumber, amount) {
    // Nunca logar o PAN completo nem a chave do gateway (finding CRITICAL da auditoria)
    logger.info(`Processando pagamento de R$ ${amount} com cartão terminado em ${cardNumber.slice(-4)}`);
    const approved = cardNumber.startsWith('4');
    return { status: approved ? 'PAID' : 'DENIED', amount };
}

module.exports = { charge };
