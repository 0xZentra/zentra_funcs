def trade_pair_create(info, args):
    # still permissionless to create a pair, but need base token owner
    assert args['f'] == 'trade_pair_create'
    # base/quote or quote1/quote2, sort quotes

