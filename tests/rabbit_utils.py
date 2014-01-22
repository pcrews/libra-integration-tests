# lbaas-rabbit-scanner
# utility script for scanning a rabbitmq queue, looking for records
# related to a specified loadbalancer id
# for testing lbaas metering and billing

from kombu import BrokerConnection, Consumer, Exchange, Queue, Connection
import sys
import time

counter = 0
lb_counter = 0
event_types = {}
lb_events = {}
byte_count = []
lb_messages = []
my_lb_id = None
my_logging = None

def on_message(body, message):
    global counter
    global lb_counter
    global lb_messages
    global lb_events
    global event_types
    global lb_id
    global byte_count
    #global my_logging
    #global my_lb_id

    data = []
    match = False
    event_type = None

    counter += 1
    my_logging.info("Record: %s" %counter)
    data.append("Details:")
    try:
        for key, value in body.items():
            data.append('\t%s: %s' %(key, value))
            if key == 'event_type':
                event_type = value
                if value in event_types:
                    event_types[value] += 1
                else:
                    event_types[value] = 1
            if key == 'payload':
               for pkey, pval in value.items():
                   data.append('\t\t%s: %s' %(pkey, pval))
                   if pkey == u'instance_id':
                       if pval == the_lb_id:
                           lb_counter += 1
                           if event_type in lb_events:
                               lb_events[event_type] += 1
                           else:
                               lb_events[event_type] = 1
                           match = True
                   if pkey == u'metrics' and match: #bandwidth message
                       bytes_sent = pval[u'metric_value']
                       byte_count.append(bytes_sent)
        data.append('='*80)
        if match:
            my_logging.info("Record for loadbalancer: %s found:" %(my_lb_id))
            my_logging.info("\n".join(data))
            lb_messages.append(body)
        #message.ack()
    except Exception, e:
        print Exception, e

def on_decode_error(message, error):
    logging.info("bad decode:\n")
    logging.info(message)
    logging.info(error)

def get_metering_data(args, lb_id, logging):
    global my_logging
    my_logging = logging
    global my_lb_id
    my_lb_id = lb_id

    mab_exchange = Exchange(args.rabbitexchange, type='topic', durable=True)
    mab_queue = Queue(args.rabbitqueue, exchange=mab_exchange, routing_key=args.rabbitroutingkey)
    connect_string = 'amqp://%s:%s@%s:%s/%s?ssl=1' %( args.rabbituser,
                                                       args.rabbitpass,
                                                       args.rabbithost,
                                                       args.rabbitport,
                                                       args.rabbitvirthost)
    logging.info(connect_string)
    with BrokerConnection(connect_string) as conn:
        logging.info("Connected: %s" %conn.connected)
        #for key, item in vars(conn).items():
        #  logging.info("%s: %s" %(key, item)
        conn.connect()
        logging.info("Connected: %s" %conn.connected)
        logging.info("Starting consumer")
        x = conn.Consumer(mab_queue, callbacks=[on_message], accept=['json'], on_decode_error=on_decode_error, auto_declare=True)
        x.consume()
        for i in range(100000):
            try:
                conn.drain_events(timeout=3)
            except Exception, e:
                logging.info(e)
                logging.info("out of messages or error, stopping...")
                break
        logging.info("Scanned %d total messages" %(counter))
        logging.info("All events:")
        for key, value in event_types.items():
            logging.info("%s: %s" %(key, value))
        logging.info("Found %d records for lb_id: %s" %(lb_counter, lb_id))
        logging.info("Record types for lb_id: %s" %(lb_id))
        for key, value in lb_events.items():
            logging.info("%s: %s" %(key, value))
        logging.info("Byte total for lb:")
        logging.info(byte_count)
        byte_total = 0
        for i in byte_count:
            byte_total += i
        logging.info("Total bytes: %d" %byte_total)
        x.recover(requeue=True)
        conn.release()
        return byte_count, lb_messages, byte_total
